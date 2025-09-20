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
from scraper.serialize import serialize
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
    except Exception as e:
        print(f'error: {e}')
        sys.exit(1)

    for node in crawled.nodes:
        print('    ' * node.depth + node.at + (' (offline)' if not node.indexed else ''))


@webchain.command
@click.argument('url', required=True)
@asyncio_click
async def json(url: str):
    try:
        crawled = await crawl(url)
    except Exception as e:
        print(f'error: {e}')
        sys.exit(1)

    serialized = serialize(crawled)
    print(serialized)

# checks for updates to the state encapsulated in res
# data will be the updated state, if there is an update, or will be 0 else.
# if data == 0, return 1 to interrupt bash
@webchain.command
@click.argument('path1', required=True, type=click.Path())
@click.argument('path2', required=True, type=click.Path())
@asyncio_click
async def patch(path1, path2) -> str|int:
    data = 0
    res = ''
    try:
        # strin = sys.stdin.read()
        # strin.rstrip('\n')
        res1 = jjson.loads(path1)
        res2 = jjson.loads(path2)
    except:
        if not res1:
            print(f"{res1} not valid JSON. Try again")
        else:
            print(f"{res2} not valid JSON. Try again")

    try:
        data = await compareState(res1, res2)
    except:
        print("Patching process failed.")

    if not data:
        sys.exit(1)
    try:
        ret = jjson.dumps(data, indent='\t')
        print(ret)
        return ret
    except:
        print("Write failed.")
