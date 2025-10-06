import asyncio
from datetime import datetime
import io
import os
import sys
from functools import wraps
import logging
import click

from scraper.crawl import crawl
from scraper.read import compareState
from scraper.metadata import enrich_with_metadata
from scraper.serialize import deserialize, serialize


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

    print('')

    for node in crawled.nodes:
        print('    ' * node.depth + node.at + (' (not crawled)' if not node.indexed else ''))

    if any(node.unqualified for node in crawled.nodes):
        print('')
        for node in crawled.nodes:
            if node.unqualified:
                print(f'{len(node.unqualified)} unqualified in {node.at} -> {node.unqualified}')

    duration = datetime.fromisoformat(crawled.end) - datetime.fromisoformat(crawled.start)

    print(f'\ncrawled {len(crawled.nodes)} nodes in {duration.total_seconds():.2f} seconds')


@webchain.command
@click.argument('url', required=True)
@asyncio_click
async def json(url: str):
    try:
        crawled = await crawl(url)
    except Exception as e:
        print(f'error: {e}')
        sys.exit(1)

    serialized = serialize(crawled, indent='\t')
    print(serialized)


# checks for updates to the state encapsulated in res
# data will be the updated state, if there is an update, or will be 0 else.
# if data == 0, return 1 to interrupt bash
@webchain.command
@click.argument('path1', required=True, type=click.File())
@click.argument('path2', required=True, type=click.File())
@asyncio_click
async def patch(path1: io.TextIOWrapper, path2: io.TextIOWrapper) -> None:
    data = 0

    try:
        res1 = deserialize(path1.read())
    except:
        print(f'{path1.name} not valid crawl json')
        sys.exit(1)

    try:
        res2 = deserialize(path2.read())
    except:
        print(f'{path2.name} not valid crawl json')
        sys.exit(1)

    data = await compareState(res1, res2)

    if not data:
        sys.exit(1)

    ret = serialize(data, indent='\t')
    print(ret)


@webchain.command
@click.argument('file', required=True, type=click.File())
@asyncio_click
async def enrich(file: io.TextIOWrapper) -> None:
    try:
        webchain = deserialize(file.read())
    except Exception as e:
        print(f'error: {e}')
        sys.exit(1)

    enriched = await enrich_with_metadata(webchain)
    serialized = serialize(enriched, indent='\t')
    print(serialized)
