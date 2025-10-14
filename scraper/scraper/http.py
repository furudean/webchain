import logging
import os

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


async def load_page_html(
    url: str,
    session: aiohttp.ClientSession,
    referrer: str | None,
) -> str | None:
    async def run():
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
            logger.info(f'invalid url {url}: ' + type(e).__name__)
            return None
        except (aiohttp.TooManyRedirects, aiohttp.RedirectClientError) as e:
            logger.info(f'bad redirects for url {url}: ' + type(e).__name__)
            return None
        except aiohttp.ClientResponseError as e:
            if 400 <= e.status < 500:
                logger.info(f'{e.status} {url}')
                return None
            logger.debug(f'{url}: ' + type(e).__name__)
            raise
        except InvalidContentType:
            logger.info(f'non-html content-type for url {url}: {content_type}')
            return None
        except aiohttp.ClientError as e:
            logger.debug(f'{url}: ' + type(e).__name__)
            raise

    attempts = int(os.environ.get('WEBCHAIN_NETWORK_ATTEMPTS', '5'))
    retrying = tenacity.AsyncRetrying(
        wait=tenacity.wait_exponential(),
        stop=tenacity.stop_after_attempt(attempts),
        reraise=True,
    )
    async for attempt in retrying:
        with attempt:
            return await run()
