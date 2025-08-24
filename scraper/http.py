import aiohttp


def get_session() -> aiohttp.ClientSession:
    return aiohttp.ClientSession(headers={"User-Agent": "webchain-scraper/DRAFT"})
