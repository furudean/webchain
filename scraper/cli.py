import asyncio
import sys

from scraper.http import get_session
from scraper.print import recursively_print_nominations

async def _print_tree():
    site = sys.argv[1] if len(sys.argv) > 1 else None

    if not site:
        print("usage: print-tree <root>")
        sys.exit(1)

    async with get_session() as session:
        await recursively_print_nominations(site, session=session)

def print_tree():
   asyncio.run(_print_tree())
