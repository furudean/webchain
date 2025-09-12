import asyncio
import os
import sys
import json as jjson
from functools import wraps
from datetime import datetime, timezone
import time
import dataclasses
import logging

import click

from scraper.crawl import crawl
from scraper.read import read_chain_into_table
from scraper.hash import HashTable


def asyncio_click(func):
    """Decorator that wraps coroutine with asyncio.run."""

    @wraps(func)
    def wrapper(*args, **kwargs):
        return asyncio.run(func(*args, **kwargs))

    return wrapper


@click.group
def webchain():
    log_level = os.environ.get('LOG_LEVEL', 'INFO').upper()
    logging.basicConfig(level=log_level, format='%(filename)s: %(message)s')
    pass


@webchain.command
@click.argument('url', required=True)
@asyncio_click
async def tree(url: str):
    try:
        crawled = await crawl(url)
        for node in crawled.nodes:
            print('    ' * node.depth + node.at + (' (offline)' if not node.indexed else ''))
    except ValueError as e:
        print(f'error: {e}')
        sys.exit(1)


@webchain.command
@click.argument('url', required=True)
@asyncio_click
async def json(url: str):
    crawled = await crawl(url)

    data = {
        'nodes': [dataclasses.asdict(node) for node in crawled.nodes],
        'nominations_limit': crawled.nominations_limit,
        'start': crawled.start,
        'end': crawled.end
    }

    print(jjson.dumps(data, indent='\t'))


@webchain.command
@asyncio_click
async def hash_test():
    start = time.time()
    T = await read_chain_into_table('https://webchain.milkmedicine.net')
    end = time.time()
    T.setStart(datetime.fromtimestamp(start, tz=timezone.utc).isoformat())
    T.setEnd(datetime.fromtimestamp(end, tz=timezone.utc).isoformat())
    # T.serialize()
    T.view(1)
    # N = HashTable()
    # N.deserialize()
    # N.view(1)
    return
