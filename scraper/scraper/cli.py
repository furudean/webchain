import asyncio
import sys
import json as jjson
from functools import wraps
from datetime import datetime, timezone
import time

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
    start = time.time()
    nodes = await crawl(url, print_error=False)
    end = time.time()

    data = {
        "nodes": [node.__dict__ for node in nodes],
        "start": datetime.fromtimestamp(start, tz=timezone.utc).isoformat(),
        "end": datetime.fromtimestamp(end, tz=timezone.utc).isoformat(),
    }

    print(jjson.dumps(data, indent='\t'))


@webchain.command
@asyncio_click
async def hash_test():
    start = time.time()
    T = await read_chain_into_table("https://webchain.milkmedicine.net")
    end = time.time()
    T.setStart(datetime.fromtimestamp(start, tz=timezone.utc).isoformat())
    T.setEnd(datetime.fromtimestamp(end, tz=timezone.utc).isoformat())
    # T.serialize()
    T.view(1)
    # N = HashTable()
    # N.deserialize()
    # N.view(1)
    return



