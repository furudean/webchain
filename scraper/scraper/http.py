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


def final_error_handler(retry_state: tenacity.RetryCallState):
    exception = retry_state.outcome.exception() if retry_state.outcome else None
    url = retry_state.args[0] if retry_state.args else '<unknown>'
    if exception is not None:
        logger.info(
            f'{url} failed after {retry_state.attempt_number} retries: {type(exception).__name__} {exception}'
        )


@tenacity.retry(
    wait=tenacity.wait_exponential(),
    stop=tenacity.stop_after_attempt(3),
    retry_error_callback=final_error_handler,
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
    except aiohttp.InvalidURL as e:
        # we assume these are permanent and do not retry
        logger.info(f'invalid url {url}: ' + type(e).__name__)
        return None
    except (aiohttp.TooManyRedirects, aiohttp.RedirectClientError) as e:
        # seems like trouble
        logger.info(f'bad redirects for url {url}: ' + type(e).__name__)
        return None
    except aiohttp.ClientResponseError as e:
        if 400 <= e.status < 500:
            # client error, do not retry
            logger.info(f'{e.status} {url}')
            return None
        logger.debug(f'{url}: ' + type(e).__name__)
        # server error, candidate for retry
        raise
    except InvalidContentType:
        logger.info(f'non-html content-type for url {url}: {content_type}')
        return None
    except aiohttp.ClientError as e:
        logger.debug(f'{url}: ' + type(e).__name__)
        raise
