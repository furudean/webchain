from urllib.parse import urlparse
from typing import Awaitable, Protocol

from bs4 import BeautifulSoup, Tag

from scraper.http import get_session, load_page_html


def validate_uri(x: str) -> bool:
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


def get_node_nominations(html: str, root: str) -> list[str] | None:
    soup = BeautifulSoup(html, 'lxml', multi_valued_attributes=None)

    if not soup.head:
        return None

    webchain_tag = soup.head.find(name='link', attrs={'rel': 'webchain'})
    if (
        webchain_tag is None
        or not isinstance(webchain_tag, Tag)
        or webchain_tag.get('href') != root
    ):
        return None

    nominations = soup.head.find_all(is_valid_nomination)

    hrefs = [str(tag.get('href')) for tag in nominations if isinstance(tag, Tag)]

    return hrefs[:2]  # only process the first two nominations


class CrawlCallback(Protocol):
    def __call__(self, nomination: str, parent: str) -> Awaitable: ...


async def crawl(root_url: str, callback: CrawlCallback) -> None:
    """
    Crawl the webchain nomination graph starting from `root`, calling `callback`
    for each valid nomination found, passing the nomination URL and its parent
    URL.
    """
    seen: set[str] = set()

    async with get_session() as session:

        async def process_node(url: str) -> None:
            if url in seen:
                return

            seen.add(url)

            html = await load_page_html(url, session=session)

            if html is None:
                # could not load page, stop recursion here
                return

            nominations = get_node_nominations(html=html, root=root_url)

            if nominations:
                for candidate_url in nominations:
                    seen.add(candidate_url)
                    # callback with nomination and its parent
                    await callback(nomination=candidate_url, parent=url)
                    # recurse into nomination
                    await process_node(candidate_url)

        await process_node(root_url)
