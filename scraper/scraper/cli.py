import asyncio
import os
import sys
import fileinput
import json as jjson
from functools import wraps
from datetime import datetime, timezone
import time
import dataclasses
import logging

import click

from scraper.crawl import crawl
from scraper.read import read_chain_into_table, compareState
from scraper.state import StateTable


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
async def patch() -> str|int:
    try:
        strin = sys.stdin.read()
        strin.rstrip('\n')
        res = jjson.loads(strin)
        data = await compareState(res)
    except:
        print("Input not valid JSON. Try again")
    if not data:
        print(1)
        return 1
    try:
        ret = jjson.dumps(data, indent='\t')
        print(ret)
        return ret
    except:
        print("Write failed.")
