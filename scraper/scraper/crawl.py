import itertools
from urllib.parse import urlparse
from dataclasses import dataclass
import asyncio
from datetime import datetime, timezone
from time import time

from bs4 import BeautifulSoup, Tag
from bs4.element import PageElement

from scraper.http import get_session, load_page_html


@dataclass
class HtmlMetadata:
    title: str | None
    description: str | None
    theme_color: str | None


@dataclass
class CrawledNode:
    at: str
    children: list[str]
    parent: str | None
    depth: int
    indexed: bool
    html_metadata: HtmlMetadata | None


def validate_uri(x: str) -> bool:
    """check if a string is a valid uri with both scheme (http/https) and netloc (domain)."""
    try:
        result = urlparse(x)
        return all([result.scheme, result.netloc])
    except AttributeError:
        return False


def is_valid_nomination(tag: Tag) -> bool:
    if not isinstance(tag, Tag) or tag.name != 'link':
        return False

    rel = tag.get('rel')
    assert isinstance(rel, str)  # is always a string with multi_valued_attributes=None

    if rel != 'webchain-nomination':
        return False

    href = tag.get('href')

    if isinstance(href, str) and validate_uri(href):
        return True

    return False


def get_node_nominations(html: str, root: str, seen: set[str] | None = None) -> list[str] | None:
    """
    extract webchain nominations from html, but only if it's a valid webchain node.
    """
    soup = BeautifulSoup(html, 'lxml', multi_valued_attributes=None)

    if seen is None:
        seen = set()

    # look for the webchain declaration link in the html. we're permissive, so
    # we search the entire document, not just the head.
    webchain_tag = soup.find(name='link', attrs={'rel': 'webchain'})
    webchain_href = str(webchain_tag.get('href')) if isinstance(webchain_tag, Tag) else None

    def normalize_url(url: str) -> str:
        return url.rstrip('/')

    if (
        webchain_tag is None
        or not isinstance(webchain_tag, Tag)
        or webchain_href is None
        or normalize_url(webchain_href) != normalize_url(root)
    ):
        return None

    nominations = soup.find_all(is_valid_nomination)

    hrefs = [
        str(tag.get('href'))
        for tag in nominations
        if isinstance(tag, Tag)
        and tag.get('href') not in seen  # any previously seen urls are already a part of the graph
    ]

    return hrefs


def handle_meta_element(node: Tag | PageElement | None) -> str | None:
    if isinstance(node, Tag) and node.get('content'):
        return str(node.get('content'))

    return None


def get_html_metadata(html: str) -> HtmlMetadata | None:
    soup = BeautifulSoup(html, 'lxml', multi_valued_attributes=None)

    if not soup.head:
        return None

    metadata = HtmlMetadata(title=None, description=None, theme_color=None)

    title_element = soup.head.title
    metadata.title = title_element.string if title_element else None
    metadata.description = handle_meta_element(
        soup.head.find('meta', attrs={'name': 'description'})
    )
    metadata.theme_color = handle_meta_element(
        soup.head.find('meta', attrs={'name': 'theme-color'})
    )

    return metadata


def get_nominations_limit(html: str, default: int | None = None) -> int | None:
    soup = BeautifulSoup(html, 'lxml', multi_valued_attributes=None)

    if not soup.head:
        return default

    limit_element = soup.find('meta', attrs={'name': 'webchain-nominations-limit'})
    limit_str = handle_meta_element(limit_element)

    if limit_str is None:
        return default

    try:
        limit = int(limit_str)
        if limit < 0:
            return default
        return limit
    except ValueError:
        return default


def to_iso_timestamp(x: float) -> str:
    return datetime.fromtimestamp(x, tz=timezone.utc).isoformat()


@dataclass
class CrawlResponse:
    nodes: list[CrawledNode]
    nominations_limit: int
    start: str
    end: str


async def crawl(root_url: str, recursion_limit: int = 1000) -> CrawlResponse:
    """
    crawl the webchain nomination graph starting from `root_url`.

    this performs a depth-first traversal of the webchain graph, following
    nomination links from each valid webchain node.

    Parameters:
        root_url: The starting URL for the crawl
        limit_nominations: Maximum number of nominations to follow from each node,
            ignoring any additional nominations. 0 means unlimited.
        recursion_limit: maximum recursion depth

    """
    seen: set[str] = set()
    nominations_limit: int | None = None
    start = time()

    async def process_node(at: str, parent: str | None = None, depth=0) -> list[CrawledNode]:
        nonlocal nominations_limit

        if at in seen:
            return []

        seen.add(at)
        html = await load_page_html(at, referrer=parent, session=session)
        nominations = None
        html_metadata = None

        if depth == 0:
            if html is None:
                raise ValueError(f'starting url {root_url} is unreachable')

            nominations_limit = get_nominations_limit(html)

            if nominations_limit is None:
                raise ValueError(
                    f'starting url {root_url} does not specify a valid nominations limit'
                )

        if html:
            nominations = get_node_nominations(html, root_url, seen)
            if nominations is not None and nominations_limit != 0:
                nominations = nominations[:nominations_limit]

            html_metadata = get_html_metadata(html)

        node = CrawledNode(
            at=at,
            children=nominations or [],
            parent=parent,
            depth=depth,
            indexed=html is not None,
            html_metadata=html_metadata,
        )
        nodes = [node]

        if nominations and depth < recursion_limit:
            tasks = [process_node(at=url, parent=at, depth=depth + 1) for url in nominations]
            results = await asyncio.gather(*tasks)

            nodes.extend(itertools.chain(*results))

        return nodes

    async with get_session() as session:
        start = time()
        nodes = await process_node(root_url)
        end = time()

        return CrawlResponse(
            nodes=nodes,
            nominations_limit=nominations_limit or 0,
            start=to_iso_timestamp(start),
            end=to_iso_timestamp(end),
        )
