import asyncio
import dataclasses
from logging import getLogger
from urllib.parse import urljoin, urlparse

import aiohttp
from bs4 import BeautifulSoup
import feedparser

from spider.robots import allowed_by_robots_txt
from spider.http import UA, get_session, get
from spider.crawl import CrawlResponse, handle_meta_element
from spider.contracts import CrawledNode, HtmlMetadata, SyndicationFeed

logger = getLogger(__name__)


def is_absolute_url(url: str) -> bool:
    return bool(urlparse(url).netloc)


def as_absolute_url(href: str, domain: str) -> str:
    if is_absolute_url(href):
        return href
    else:
        return urljoin(domain, href)


def get_html_metadata(html: str, at: str) -> HtmlMetadata | None:
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


async def get_syndication_feeds(
    html: str, at: str, session: aiohttp.ClientSession
) -> list[SyndicationFeed]:
    def parse_syndication_feed(xml: str, url: str) -> SyndicationFeed | None:
        d = feedparser.parse(xml)

        return SyndicationFeed(
            url=url,
            title=d.feed.get("title"),
            description=d.feed.get("description"),
            published=d.feed.get("published"),
            updated=d.feed.get("updated"),
            version=d.get("version"),
        )

    async def fetch_pair(url, session):
        xml = await get(url, session=session, referrer=at)
        return (url, xml)

    soup = BeautifulSoup(html, "lxml", multi_valued_attributes=None)

    syndication_links = soup.head.find_all(
        "link", attrs={"type": ["application/rss+xml", "application/atom+xml"]}
    )

    syndication_urls = list(
        dict.fromkeys(as_absolute_url(link.get("href"), domain=at) for link in syndication_links)
    )

    syndication_data = await asyncio.gather(*[fetch_pair(url, session) for url in syndication_urls])

    return [parse_syndication_feed(xml, url=url) for url, xml in syndication_data]


async def fetch_and_update_metadata(
    node: CrawledNode, session: aiohttp.ClientSession, check_robots_txt=False
) -> CrawledNode:
    """Returns a new CrawledNode with updated metadata"""

    node_copy = CrawledNode(**dataclasses.asdict(node))

    if check_robots_txt and not (
        await allowed_by_robots_txt(node.at, user_agent=UA, session=session)
    ):
        logger.info(f"disallowed by robots.txt: {node.at}")
        return node_copy

    if node.indexed:
        try:
            html = await get(node.at, referrer=node.parent, session=session)

            if html:
                node_copy.html_metadata = get_html_metadata(html, at=node.at)
                node_copy.syndication_feeds = await get_syndication_feeds(
                    html, at=node.at, session=session
                )
        except Exception as e:
            logger.warning(f"failed to fetch metadata for {node.at}: " + type(e).__name__)
            raise e

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
