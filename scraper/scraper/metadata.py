import asyncio
import dataclasses

import aiohttp
from bs4 import BeautifulSoup
from scraper.http import get_session, load_page_html
from scraper.crawl import CrawlResponse, handle_meta_element
from scraper.contracts import CrawledNode, CrawledNodeWithMetadata, HtmlMetadata


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


async def fetch_and_update_metadata(
    node: CrawledNode | CrawledNodeWithMetadata, session: aiohttp.ClientSession
) -> CrawledNodeWithMetadata:
    html_metadata: HtmlMetadata | None = None

    if node.indexed:
        html = await load_page_html(node.at, referrer=node.parent, session=session)

        if html:
            html_metadata = get_html_metadata(html)

    return CrawledNodeWithMetadata(
        **dataclasses.asdict(node),
        # keep old metadata if fetching failed
        html_metadata=html_metadata if html_metadata else getattr(node, 'html_metadata', None),
    )


async def enrich_with_metadata(crawl_response: CrawlResponse) -> CrawlResponse:
    async with get_session() as session:
        tasks = []
        for node in crawl_response.nodes:
            tasks.append(fetch_and_update_metadata(node, session))

        nodes = await asyncio.gather(*tasks)

    crawl_response_dict = dataclasses.asdict(crawl_response)
    crawl_response_dict['nodes'] = nodes
    return CrawlResponse(**crawl_response_dict)
