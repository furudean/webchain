import asyncio
import dataclasses
from logging import getLogger

import aiohttp
from bs4 import BeautifulSoup
from spider.robots import allowed_by_robots_txt
from spider.http import UA, get_session, load_page_html
from spider.crawl import CrawlResponse, handle_meta_element
from spider.contracts import CrawledNode, HtmlMetadata

logger = getLogger(__name__)


def get_html_metadata(html: str) -> HtmlMetadata | None:
    soup = BeautifulSoup(html, "lxml", multi_valued_attributes=None)

    if not soup.head:
        return None

    metadata = HtmlMetadata(title=None, description=None, theme_color=None)

    title_element = soup.head.title
    metadata.title = title_element.string if title_element else None
    if not metadata.title:
        metadata.title = handle_meta_element(soup.head.find("meta", attrs={"property": "og:title"}))
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
    node: CrawledNode, session: aiohttp.ClientSession, check_robots_txt=False
) -> CrawledNode:
    """Returns a new CrawledNode with updated metadata"""

    if check_robots_txt and not (
        await allowed_by_robots_txt(node.at, user_agent=UA, session=session)
    ):
        logger.info(f"disallowed by robots.txt: {node.at}")
        return node

    node_copy = CrawledNode(**dataclasses.asdict(node))

    if node.indexed:
        html = await load_page_html(node.at, referrer=node.parent, session=session)

        if html:
            node_copy.html_metadata = get_html_metadata(html)

    return node_copy


async def enrich_with_metadata(
    crawl_response: CrawlResponse, check_robots_txt=False
) -> CrawlResponse:
    async with get_session() as session:
        tasks = []
        for node in crawl_response.nodes:
            tasks.append(
                fetch_and_update_metadata(node, check_robots_txt=check_robots_txt, session=session)
            )

        nodes = await asyncio.gather(*tasks)

    crawl_response_dict = dataclasses.asdict(crawl_response)
    crawl_response_dict["nodes"] = nodes
    return CrawlResponse(**crawl_response_dict)
