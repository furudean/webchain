import logging
import os
from urllib import robotparser
from urllib.parse import urljoin

import aiohttp
import tenacity

logger = logging.getLogger(__name__)


async def get_robots_txt(
    url: str,
    session: aiohttp.ClientSession,
) -> str | None:
    base_url = urljoin(url, "/")
    robots_url = urljoin(base_url, "/robots.txt")

    try:
        async with session.get(
            robots_url,
            headers={"Accept": "text/plain"},
            timeout=aiohttp.ClientTimeout(total=5),
        ) as response:
            text = await response.text()
            logger.debug(f"got {robots_url}")
        return text
    except aiohttp.ClientResponseError as e:
        if e.code == 404:
            return None
        else:
            raise e
    except (aiohttp.ClientError, aiohttp.ClientConnectorDNSError) as e:
        logger.debug(f"failed to fetch {robots_url}: " + type(e).__name__)
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
