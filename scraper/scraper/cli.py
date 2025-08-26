import asyncio
import sys
import json

from scraper.crawl import crawl
from scraper.read import recursively_read_nodes


async def _get_tree():
    url = sys.argv[1] if len(sys.argv) > 1 else None

    if not url:
        print('usage: tree <root>')
        sys.exit(1)

    try:
        for node in await crawl(url):
            print('    ' * node.depth + node.at + (' (offline)' if not node.indexed else ''))
    except ValueError as e:
        print(f'error: {e}')
        sys.exit(1)


def get_tree():
    asyncio.run(_get_tree())


async def _get_json():
    url = sys.argv[1] if len(sys.argv) > 1 else None

    if not url:
        print('usage: tree <root>')
        sys.exit(1)

    nodes = await crawl(url)
    print(json.dumps([node.__dict__ for node in nodes], indent=2))

def get_json():
    asyncio.run(_get_json())


async def _read_tree():
    site = sys.argv[1] if len(sys.argv) > 1 else None

    if not site:
        print('usage: read-tree <root>')
        sys.exit(1)

    await recursively_read_nodes(site)


def read_tree():
    asyncio.run(_read_tree())
