import aiohttp
from tenacity import retry, stop_after_attempt, wait_exponential


def get_session() -> aiohttp.ClientSession:
    return aiohttp.ClientSession(
        headers={'User-Agent': 'webchain-scraper/DRAFT'}, raise_for_status=True
    )


class InvalidContentType(Exception):
    pass


@retry(
    wait=wait_exponential(),
    stop=stop_after_attempt(5),
    retry_error_callback=lambda state: None,  # return None if retries fail
)
async def load_page_html(
    url: str, session: aiohttp.ClientSession, referrer: str | None
) -> str | None:
    try:
        headers = {}
        if referrer is not None:
            headers['Referer'] = referrer

        async with session.get(
            url, timeout=aiohttp.ClientTimeout(total=5), headers=headers
        ) as response:
            content_type = response.headers.get('Content-Type', '')
            if not content_type.startswith('text/html'):
                raise InvalidContentType
            html = await response.text()
        return html
    except (
        aiohttp.ServerConnectionError,
        aiohttp.ServerTimeoutError,
    ) as e:
        # server returned no response at all. candidate for retry
        print(f'server connection error for url {url}: ' + type(e).__name__)
        raise
    except (aiohttp.InvalidURL, aiohttp.ClientConnectionError) as e:
        # some kind of low-level connection error (DNS failure, refused connection, etc)
        # we assume these are permanent and do not retry
        print(f'could not connect to {url}: ' + type(e).__name__)
        return None
    except (aiohttp.TooManyRedirects, aiohttp.RedirectClientError) as e:
        print(f'bad redirects for url {url}: ' + type(e).__name__)
        return None
    except aiohttp.ClientResponseError as e:
        print(f'{e.status} url {url}')
        if 400 <= e.status < 500:
            # client error, do not retry
            return None
        # server error, candidate for retry
        raise
    except InvalidContentType:
        print(f'non-html content-type for url {url}: {content_type}')
        return None
