import asyncio
import sys
import json as jjson
from functools import wraps
from datetime import datetime, timezone

import click

from scraper.crawl import crawl
from scraper.read import read_chain_into_table
from scraper.hash import HashTable

def asyncio_click(func):
    '''Decorator that wraps coroutine with asyncio.run.'''
    @wraps(func)
    def wrapper(*args, **kwargs):
        return asyncio.run(func(*args, **kwargs))
    return wrapper


@click.group
def webchain():
    pass


@webchain.command
@click.argument('url', required=True)
@asyncio_click
async def tree(url: str):
    try:
        for node in await crawl(url):
            print('    ' * node.depth + node.at + (' (offline)' if not node.indexed else ''))
    except ValueError as e:
        print(f'error: {e}')
        sys.exit(1)


@webchain.command
@click.argument('url', required=True)
@asyncio_click
async def json(url: str):
    nodes = await crawl(url, print_error=False)

    data = {
        "nodes": [node.__dict__ for node in nodes],
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }

    print(jjson.dumps(data, indent='\t'))


@webchain.command
@click.argument('insite', required=True)
@asyncio_click
async def read_tree(insite=None) -> HashTable:
    if not insite:
        site = sys.argv[1] if len(sys.argv) > 1 else None

        if not site:
            print('usage: read-tree <root>')
            sys.exit(1)

        return await read_chain_into_table(site)
    else:
        return await read_chain_into_table(insite)


@webchain.command
@asyncio_click
def hash_test():
    root = "https://chain-staging.milkmedicine.net"
    T = read_tree(root)

    found_node = T.findValue("https://chain-staging.milkmedicine.net/b/1")
    print(found_node)
    found_child = T.findValue(found_node.children[1])
    print(found_child)
    return
