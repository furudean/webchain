import logging

import aiohttp
import tenacity

logger = logging.getLogger()


def get_session() -> aiohttp.ClientSession:
    return aiohttp.ClientSession(
        headers={'User-Agent': 'webchain-scraper/DRAFT', 'Accept-Language': 'en-US, *;q=0.5'},
        raise_for_status=True,
        cookie_jar=aiohttp.DummyCookieJar(),
        trust_env=True,
    )


class InvalidContentType(Exception):
    pass


@tenacity.retry(
    wait=tenacity.wait_exponential(),
    stop=tenacity.stop_after_attempt(3),
    retry_error_callback=lambda state: None,  # return None if retries fail
)
async def load_page_html(
    url: str,
    session: aiohttp.ClientSession,
    referrer: str | None,
) -> str | None:
    try:
        headers = {}
        if referrer is not None:
            headers['Referer'] = referrer

        logger.debug(f'get {url}')
        async with session.get(
            url, timeout=aiohttp.ClientTimeout(total=5), headers=headers
        ) as response:
            content_type = response.headers.get('Content-Type', '')
            if not content_type.startswith('text/html'):
                raise InvalidContentType
            html = await response.text()
            logger.debug(f'got {url}')
        return html
    except (
        aiohttp.ServerConnectionError,
        aiohttp.ServerTimeoutError,
    ) as e:
        # server returned no response at all. candidate for retry
        logger.info(f'server connection error for url {url}: ' + type(e).__name__)
        raise
    except aiohttp.InvalidURL as e:
        # some kind of low-level connection error (refused connection, etc)
        # we assume these are permanent and do not retry
        logger.info(f'could not connect to {url}: ' + type(e).__name__)
        return None
    except (aiohttp.TooManyRedirects, aiohttp.RedirectClientError) as e:
        logger.info(f'bad redirects for url {url}: ' + type(e).__name__)
        return None
    except aiohttp.ClientResponseError as e:
        logger.info(f'{e.status} {url}')
        if 400 <= e.status < 500:
            # client error, do not retry
            return None
        # server error, candidate for retry
        raise
    except InvalidContentType:
        logger.info(f'non-html content-type for url {url}: {content_type}')
        return None
    except aiohttp.ClientError as e:
        logger.info(f'{url}: ' + type(e).__name__)
        raise
