import asyncio
import sys

from scraper.crawl import crawl


async def _print_tree():
    url = sys.argv[1] if len(sys.argv) > 1 else None

    if not url:
        print('usage: print-tree <root>')
        sys.exit(1)

    for node in await crawl(url):
        print('    ' * node.depth + node.at + (' (offline)' if not node.indexed else ''))


def print_tree():
    asyncio.run(_print_tree())
