import itertools
from urllib.parse import urlparse
from dataclasses import dataclass
import asyncio

from bs4 import BeautifulSoup, Tag

from scraper.http import get_session, load_page_html


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


def get_node_nominations(html: str, root: str, seen: set[str]) -> list[str] | None:
    """
    extract webchain nominations from html, but only if it's a valid webchain node.
    """
    soup = BeautifulSoup(html, 'lxml', multi_valued_attributes=None)

    if not soup.head:
        return None

    # look for the webchain declaration link in the head
    webchain_tag = soup.head.find(name='link', attrs={'rel': 'webchain'})
    if (
        webchain_tag is None
        or not isinstance(webchain_tag, Tag)
        or webchain_tag.get('href') != root  # must point to the root url
    ):
        return None

    nominations = soup.head.find_all(is_valid_nomination)

    hrefs = [
        str(tag.get('href'))
        for tag in nominations
        if isinstance(tag, Tag)
        and tag.get('href') not in seen  # any previously seen urls are already a part of the graph
    ]

    return hrefs[:2]  # only process the first two nominations


@dataclass
class CrawledNode:
    at: str
    children: list[str]
    parent: str | None
    depth: int
    indexed: bool


async def crawl(root_url: str) -> list[CrawledNode]:
    """
    crawl the webchain nomination graph starting from `root_url`.

    this performs a depth-first traversal of the webchain graph, following
    nomination links from each valid webchain node.

    returns a list of all nodes visited.
    """
    seen: set[str] = set()

    async def process_node(at: str, parent: str | None = None, depth=0) -> list[CrawledNode]:
        if at in seen:
            return []

        seen.add(at)
        html = await load_page_html(at, session=session)
        nominations = get_node_nominations(html, root_url, seen) if html else None

        if depth == 0 and nominations is None:
            raise ValueError(
                f'starting url {root_url} has no nominations or is not a valid webchain node'
            )

        node = CrawledNode(
            at=at,
            children=nominations or [],
            parent=parent,
            depth=depth,
            indexed=html is not None,
        )
        nodes = [node]

        if nominations:
            tasks = [process_node(url, at, depth + 1) for url in nominations]
            results = await asyncio.gather(*tasks)

            nodes.extend(itertools.chain(*results))

        return nodes

    async with get_session() as session:
        return await process_node(root_url)
