from urllib.parse import urlparse

import aiohttp
from bs4 import BeautifulSoup, Tag

def validate_uri(x: str) -> bool:
    try:
        result = urlparse(x)
        return all([result.scheme, result.netloc])
    except AttributeError:
        return False


async def load_page_html(url: str, session: aiohttp.ClientSession) -> str:
    async with session.get(url) as response:
        response.raise_for_status()  # TODO: handle errors with retry
        html = await response.text()

    return html

def is_valid_nomination(tag: Tag) -> bool:
    # print(tag)
    if not isinstance(tag, Tag) or tag.name != 'link':
        return False

    rel = tag.get('rel')
    assert isinstance(rel, str) # is always a string with multi_valued_attributes=None

    if rel != 'webchain-nomination':
        return False

    href = tag.get('href')

    if isinstance(href, str) and validate_uri(href):
        return True

    return False

async def get_node_nominations(html: str, root: str) -> list[str] | None:
    soup = BeautifulSoup(html, 'lxml', multi_valued_attributes=None)

    if not soup.head:
        return None

    webchain_tags = soup.head.find(name='link', attrs={'rel': 'webchain'})
    # print("found webchain tags:", webchain_tags)
    if webchain_tags is None or not isinstance(webchain_tags, Tag) or webchain_tags.get('href') != root:
        return None

    nominations = soup.head.find_all(is_valid_nomination)

    return [str(tag.get('href')) for tag in nominations[:2] if isinstance(tag, Tag)]
