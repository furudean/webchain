import itertools
import sys
from urllib.parse import urlparse
import asyncio
from datetime import datetime, timezone
from time import time
from logging import getLogger

from bs4 import BeautifulSoup, Tag
from bs4.element import PageElement
from ordered_set import OrderedSet

from spider.http import get_session, load_page_html
from spider.contracts import CrawlResponse, CrawledNode

logger = getLogger(__name__)


def validate_uri(x: str) -> bool:
    """check if a string is a valid uri with both scheme (http/https) and netloc (domain)."""
    try:
        result = urlparse(x)
        return all([result.scheme, result.netloc])
    except AttributeError:
        return False


def is_valid_nomination(tag: Tag) -> bool:
    if not isinstance(tag, Tag) or tag.name != "link":
        return False

    rel = tag.get("rel")
    assert isinstance(rel, str)  # is always a string with multi_valued_attributes=None

    if rel != "webchain-nomination":
        return False

    href = tag.get("href")

    if isinstance(href, str) and validate_uri(href):
        return True

    return False


def get_raw_nominations(html: str, root: str) -> OrderedSet[str]:
    """
    extract valid webchain nominations from html
    """
    soup = BeautifulSoup(html, "lxml", multi_valued_attributes=None)

    hrefs: OrderedSet[str] = OrderedSet([])

    # look for the webchain declaration link in the html. we're permissive, so
    # we search the entire document, not just the head.
    webchain_tag = soup.find(name="link", attrs={"rel": "webchain"})
    webchain_href = (
        str(webchain_tag.get("href")) if isinstance(webchain_tag, Tag) else None
    )

    def normalize_url(url: str) -> str:
        return url.rstrip("/")

    if (
        webchain_tag is None
        or not isinstance(webchain_tag, Tag)
        or webchain_href is None
        or normalize_url(webchain_href) != normalize_url(root)
    ):
        return hrefs

    nominations = soup.find_all(is_valid_nomination)

    for tag in nominations:
        if not isinstance(tag, Tag):
            continue
        href = tag.get("href")
        if isinstance(href, str):
            hrefs.add(href)

    return hrefs


def without_trailing_slash(url: str) -> str:
    return url.rstrip("/")


def handle_meta_element(node: Tag | PageElement | None) -> str | None:
    if isinstance(node, Tag) and node.get("content"):
        content = str(node.get("content"))
        return content.replace("\n", " ").strip()

    return None


def get_nominations_limit(html: str, default: int | None = None) -> int | None:
    soup = BeautifulSoup(html, "lxml", multi_valued_attributes=None)

    if not soup.head:
        return default

    limit_element = soup.find("meta", attrs={"name": "webchain-nominations-limit"})
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
    nominations_limit: int = sys.maxsize * 2 + 1
    start = time()

    async def process_node(
        url: str, parent: str | None = None, depth=0
    ) -> list[CrawledNode]:
        nonlocal nominations_limit

        at = without_trailing_slash(url)
        seen.add(at)
        index_error: Exception | None = None
        try:
            html = await load_page_html(url, referrer=parent, session=session)
        except Exception as e:
            logger.info(f"get {url} failed after retries: {type(e).__name__} {e}")
            html = None
            index_error = e

        nominations: list[str] = []
        unqualified: list[str] = []

        if depth == 0:
            if html is None:
                raise ValueError(f"starting url {root_url} is unreachable")

            fetched_nominations_limit = get_nominations_limit(html)
            if fetched_nominations_limit is not None:
                nominations_limit = fetched_nominations_limit

            if nominations_limit is None:
                logger.error(
                    f"starting url {root_url} does not specify a nominations limit, using unlimited"
                )

        if html:
            node_nominations = OrderedSet(
                map(without_trailing_slash, get_raw_nominations(html, root_url))
            )
            nominations = list(node_nominations.difference(seen))
            extra_nominations = nominations[nominations_limit:]
            nominations = nominations[:nominations_limit]
            unqualified = list(
                node_nominations.intersection(seen).union(extra_nominations)
            )

        node = CrawledNode(
            at=at,
            children=nominations,
            unqualified=unqualified,
            parent=parent,
            depth=depth,
            indexed=html is not None,
            index_error=index_error,
        )
        nodes = [node]

        if nominations and depth < recursion_limit:
            tasks = [
                process_node(url=child_url, parent=at, depth=depth + 1)
                for child_url in nominations
            ]
            results = await asyncio.gather(*tasks)

            nodes.extend(itertools.chain(*results))

        return nodes

    async with get_session() as session:
        start = time()
        nodes = await process_node(root_url)
        end = time()

        return CrawlResponse(
            nodes=nodes,
            nominations_limit=nominations_limit,
            start=to_iso_timestamp(start),
            end=to_iso_timestamp(end),
        )
