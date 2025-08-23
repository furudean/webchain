import asyncio
import aiohttp

from scraper.print import recursively_print_nominations


async def main():
    async with aiohttp.ClientSession() as session:
        await recursively_print_nominations(
            "https://chain-staging.milkmedicine.net",
            session=session
        )

def run():
   asyncio.run(main())

if __name__ == "__main__":
    run()
