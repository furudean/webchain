import logging
import os

import aiohttp
import tenacity

from spider.error import InvalidStatusCode
from spider.cached_session import CachedClientSession
from spider.contracts import OnRetry, OnCacheHit

logger = logging.getLogger(__name__)

UA = "WebchainSpider (+https://github.com/furudean/webchain)"


def get_session() -> aiohttp.ClientSession:
    kwargs = dict(
        headers={"User-Agent": UA, "Accept-Language": "en-US, *;q=0.5"},
        raise_for_status=True,
        cookie_jar=aiohttp.DummyCookieJar(),
        trust_env=True,
    )
    if os.environ.get("WEBCHAIN_NO_CACHE"):
        return aiohttp.ClientSession(**kwargs)
    return CachedClientSession(**kwargs)


async def get(
    url: str,
    session: aiohttp.ClientSession,
    referrer: str | None = None,
    on_retry: OnRetry | None = None,
    on_cache_hit: OnCacheHit | None = None,
) -> str:
    async def run():
        headers = {}
        if referrer is not None:
            headers["Referer"] = referrer

        try:
            async with session.get(
                url, timeout=aiohttp.ClientTimeout(total=10), headers=headers
            ) as response:
                result = await response.text()
                logger.debug(f"got {url}")
                if on_cache_hit and getattr(response, "from_cache", False):
                    on_cache_hit(url)
            return result

        except aiohttp.InvalidURL as e:
            logger.info(f"invalid url {url}: " + type(e).__name__)
            raise
        except aiohttp.ClientSSLError as e:
            logger.info(f"SSL error {url}: {type(e).__name__} {e}")
            raise
        except aiohttp.ClientConnectorDNSError as e:
            logger.info(f"dns error {url}: {type(e).__name__} {e}")
            raise
        except aiohttp.ClientResponseError as e:
            if 400 <= e.status < 500:
                raise InvalidStatusCode(e.status, e.message) from e
            logger.debug(f"{url}: " + type(e).__name__)
            raise
        except aiohttp.ClientError as e:
            logger.debug(f"{url}: " + type(e).__name__, exc_info=e)
            raise

    def before_sleep(retry_state: tenacity.RetryCallState) -> None:
        if on_retry:
            on_retry(url, retry_state.attempt_number)

    attempts = int(os.environ.get("WEBCHAIN_NETWORK_ATTEMPTS", "5"))
    retrying = tenacity.AsyncRetrying(
        wait=tenacity.wait_exponential(),
        stop=tenacity.stop_after_attempt(attempts),
        retry=tenacity.retry_if_exception(
            lambda e: isinstance(e, (
                aiohttp.ClientResponseError,
                aiohttp.ClientConnectionError,
                aiohttp.ServerConnectionError,
                TimeoutError,
            )) and not isinstance(e, (
                aiohttp.ClientConnectorCertificateError,
                aiohttp.ClientConnectorDNSError,
            ))
        ),
        reraise=True,
        before_sleep=before_sleep,
    )
    async for attempt in retrying:
        with attempt:
            return await run()
