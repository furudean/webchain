import asyncio
import dataclasses

import aiohttp
from bs4 import BeautifulSoup
from spider.http import get_session, load_page_html
from spider.crawl import CrawlResponse, handle_meta_element
from spider.contracts import CrawledNode, HtmlMetadata


def get_html_metadata(html: str) -> HtmlMetadata | None:
    soup = BeautifulSoup(html, "lxml", multi_valued_attributes=None)

    if not soup.head:
        return None

    metadata = HtmlMetadata(title=None, description=None, theme_color=None)

    title_element = soup.head.title
    metadata.title = title_element.string if title_element else None
    if not metadata.title:
        metadata.title = handle_meta_element(
            soup.head.find("meta", attrs={"property": "og:title"})
        )
    if not metadata.title:
        metadata.title = handle_meta_element(
            soup.head.find("meta", attrs={"name": "twitter:title"})
        )

    if metadata.title:
        metadata.title = metadata.title.replace("\n", " ").strip()

    metadata.description = handle_meta_element(
        soup.head.find("meta", attrs={"name": "description"})
    )
    if not metadata.description:
        metadata.description = handle_meta_element(
            soup.head.find("meta", attrs={"property": "og:description"})
        )
    if not metadata.description:
        metadata.description = handle_meta_element(
            soup.head.find("meta", attrs={"name": "twitter:description"})
        )

    metadata.theme_color = handle_meta_element(
        soup.head.find("meta", attrs={"name": "theme-color"})
    )

    return metadata


async def fetch_and_update_metadata(
    node: CrawledNode | CrawledNode, session: aiohttp.ClientSession
) -> CrawledNode:
    node_dict = dataclasses.asdict(node)

    if node.indexed:
        html = await load_page_html(node.at, referrer=node.parent, session=session)

        if html:
            node_dict["html_metadata"] = get_html_metadata(html)

    return CrawledNode(**node_dict)


async def enrich_with_metadata(crawl_response: CrawlResponse) -> CrawlResponse:
    async with get_session() as session:
        tasks = []
        for node in crawl_response.nodes:
            tasks.append(fetch_and_update_metadata(node, session))

        nodes = await asyncio.gather(*tasks)

    crawl_response_dict = dataclasses.asdict(crawl_response)
    crawl_response_dict["nodes"] = nodes
    return CrawlResponse(**crawl_response_dict)
