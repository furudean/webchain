from urllib.parse import urlparse
from typing import Protocol

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


class NodeCallback(Protocol):
    def __call__(self, at: str, children: list[str], parent: str | None, depth: int) -> None: ...


async def crawl(root_url: str, node_callback: NodeCallback) -> None:
    """
    crawl the webchain nomination graph starting from `root_url`, calling
    `node_callback` for each node visited.

    this performs a depth-first traversal of the webchain graph, following
    nomination links from each valid webchain node.
    """
    seen: set[str] = set()  # track visited urls to prevent infinite loops

    async def process_node(at: str, parent: str | None = None, depth=0) -> None:
        # prevent cycles
        if at in seen:
            return

        seen.add(at)

        html = await load_page_html(at, session=session)

        if html is None:
            # failed to load page - call callback with empty nominations
            node_callback(at=at, children=[], parent=parent, depth=depth)
            return

        nominations = get_node_nominations(html=html, root=root_url, seen=seen)
        node_callback(at=at, children=nominations or [], parent=parent, depth=depth)

        if nominations:
            for candidate in nominations:
                await process_node(candidate, parent=at, depth=depth + 1)

    async with get_session() as session:
        await process_node(root_url)
