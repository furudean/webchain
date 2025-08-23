import asyncio
import aiohttp
import sys

from scraper.print import recursively_print_nominations

async def _print_tree():
    site = sys.argv[1] if len(sys.argv) > 1 else None

    if not site:
        print("usage: print-tree <root>")
        sys.exit(1)

    async with aiohttp.ClientSession() as session:
        await recursively_print_nominations(site, session=session)

def print_tree():
   asyncio.run(_print_tree())
