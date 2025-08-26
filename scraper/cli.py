import asyncio
import sys

from scraper.print import recursively_print_nominations
from scraper.read import read_chain
from scraper.crawl import get_session


async def _print_tree():
    site = sys.argv[1] if len(sys.argv) > 1 else None

    if not site:
        print('usage: print-tree <root>')
        sys.exit(1)

    await recursively_print_nominations(site)

def print_tree():
    asyncio.run(_print_tree())
