import logging
import os
from urllib import robotparser
from urllib.parse import urljoin

import aiohttp
import tenacity
from spider.http import InvalidContentType

logger = logging.getLogger(__name__)


class RobotsExclusionError(Exception):
    pass


async def get_robots_txt(
    url: str,
    session: aiohttp.ClientSession,
) -> str | None:
    base_url = urljoin(url, "/")
    robots_url = urljoin(base_url, "/robots.txt")
    try:
        # First, try HEAD request
        async with session.head(
            robots_url,
            timeout=aiohttp.ClientTimeout(total=5),
            headers={
                "Accept": "text/plain",
            },
        ) as head_response:
            content_type = head_response.headers.get("Content-Type", "")
            if not content_type.startswith("text/plain"):
                raise InvalidContentType(url=url, content_type=content_type)
    except aiohttp.ClientResponseError as e:
        if 400 <= e.status < 500:
            logger.debug(f"HEAD request failed for {robots_url}: {head_response.status}")
            return None
        logger.debug(f"HEAD request attempt failed for {robots_url}: " + type(e).__name__)
        raise

    try:
        async with session.get(robots_url, timeout=aiohttp.ClientTimeout(total=5)) as response:
            text = await response.text()
            logger.debug(f"got {robots_url}")
        return text
    except (aiohttp.ClientError, InvalidContentType) as e:
        logger.debug(f"failed to get robots.txt from {robots_url}: " + type(e).__name__)
        return None


async def allowed_by_robots_txt(
    url: str,
    user_agent: str,
    session: aiohttp.ClientSession,
) -> bool:
    async def run() -> bool:
        robots_txt = await get_robots_txt(url, session)
        if robots_txt is None:
            return True  # assume allowed if we can't fetch robots.txt

        rp = robotparser.RobotFileParser()
        rp.parse(robots_txt.splitlines())
        return rp.can_fetch(user_agent, url)

    attempts = int(os.environ.get("WEBCHAIN_NETWORK_ATTEMPTS", "5"))
    retrying = tenacity.AsyncRetrying(
        wait=tenacity.wait_exponential(),
        stop=tenacity.stop_after_attempt(attempts),
        retry_error_callback=lambda retry_state: True,  # if all attempts fail, assume its ok
    )
    async for attempt in retrying:
        with attempt:
            return await run()

    return True
