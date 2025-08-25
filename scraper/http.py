import aiohttp


def get_session() -> aiohttp.ClientSession:
    return aiohttp.ClientSession(headers={"User-Agent": "webchain-scraper/DRAFT"})


async def load_page_html(url: str, session: aiohttp.ClientSession) -> str | None:
    try:
        async with session.get(url) as response:
            response.raise_for_status()
            html = await response.text()
        return html
    except (aiohttp.ClientError, aiohttp.ServerTimeoutError, aiohttp.ClientResponseError):
        return None

