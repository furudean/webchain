import asyncio
import sys
import json
import logging
import os

from scraper.crawl import crawl
from scraper.read import read_chain_into_table
from scraper.hash import HashTable

def setup_logging(level='INFO'):
    logging.basicConfig(level=os.environ.get('LOGLEVEL', level).upper())

async def _get_tree():
    url = sys.argv[1] if len(sys.argv) > 1 else None

    if not url:
        print('usage: tree <url>')
        sys.exit(1)

    try:
        for node in await crawl(url):
            print('    ' * node.depth + node.at + (' (offline)' if not node.indexed else ''))
    except ValueError as e:
        print(f'error: {e}')
        sys.exit(1)


def get_tree():
    setup_logging()
    asyncio.run(_get_tree())


async def _get_json():
    url = sys.argv[1] if len(sys.argv) > 1 else None

    if not url:
        print('usage: json <url>')
        sys.exit(1)

    nodes = await crawl(url)
    print(json.dumps([node.__dict__ for node in nodes], indent='\t'))


def get_json():
    setup_logging(level='ERROR')
    asyncio.run(_get_json())


async def _read_tree(insite=None) -> HashTable:
    if not insite:
        site = sys.argv[1] if len(sys.argv) > 1 else None

        if not site:
            print('usage: read-tree <root>')
            sys.exit(1)

        return await read_chain_into_table(site)
    else:
        return await read_chain_into_table(insite)

def read_tree(root) -> HashTable:
    return asyncio.run(_read_tree(root))

def hash_test():
    root = "https://chain-staging.milkmedicine.net"
    T = read_tree(root)

    found_node = T.findValue("https://chain-staging.milkmedicine.net/b/1")
    print(found_node)
    found_child = T.findValue(found_node.children[1])
    print(found_child)
    return
