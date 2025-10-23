import logging
import os

import aiohttp
import tenacity

logger = logging.getLogger(__name__)

UA = "WebchainSpider (+https://github.com/furudean/webchain)"


def get_session() -> aiohttp.ClientSession:
    return aiohttp.ClientSession(
        headers={"User-Agent": UA, "Accept-Language": "en-US, *;q=0.5"},
        raise_for_status=True,
        cookie_jar=aiohttp.DummyCookieJar(),
        trust_env=True,
    )


class InvalidContentType(Exception):
    pass


async def load_page_html(
    url: str,
    session: aiohttp.ClientSession,
    referrer: str | None,
) -> str | None:
    async def run():
        headers = {}
        if referrer is not None:
            headers["Referer"] = referrer

        try:
            # HEAD request to check if robots.txt exists
            async with session.head(
                url, timeout=aiohttp.ClientTimeout(total=5), headers=headers
            ) as head_response:
                content_type = head_response.headers.get("Content-Type", "")
                if not (
                    content_type.startswith("text/html")
                    or content_type.startswith("application/xhtml+xml")
                ):
                    raise InvalidContentType

            logger.debug(f"get {url}")
            async with session.get(
                url, timeout=aiohttp.ClientTimeout(total=10), headers=headers
            ) as response:
                html = await response.text()
                logger.debug(f"got {url}")
            return html

        except aiohttp.InvalidURL as e:
            logger.info(f"invalid url {url}: " + type(e).__name__)
            return None
        except aiohttp.ClientSSLError as e:
            logger.info(f"SSL error for url {url}: {type(e).__name__} {e}")
            return None
        except aiohttp.ClientResponseError as e:
            if 400 <= e.status < 500:
                logger.info(f"GET {url}: bad status code {e}")
                return None  # don't retry on 4xx errors
            logger.debug(f"{url}: " + type(e).__name__)
            raise
        except InvalidContentType:
            logger.info(f"non-html content-type for url {url}: {content_type}")
            raise
        except aiohttp.ClientError as e:
            logger.debug(f"{url}: " + type(e).__name__)
            raise

    attempts = int(os.environ.get("WEBCHAIN_NETWORK_ATTEMPTS", "5"))
    retrying = tenacity.AsyncRetrying(
        wait=tenacity.wait_exponential(),
        stop=tenacity.stop_after_attempt(attempts),
        retry=tenacity.retry_if_exception_type(
            (
                aiohttp.ClientResponseError,
                aiohttp.ClientConnectionError,
                aiohttp.ServerConnectionError,
                TimeoutError,
            )
        ),
        reraise=True,
    )
    async for attempt in retrying:
        with attempt:
            return await run()
