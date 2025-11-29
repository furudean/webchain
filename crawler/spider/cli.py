import asyncio
from datetime import datetime
import io
import os
import sys
from functools import wraps
import logging
import click

from spider.crawl import crawl
from spider.state import patch_state
from spider.metadata import enrich_with_metadata
from spider.serialize import deserialize, serialize


def asyncio_click(func):
    """Decorator that wraps coroutine with asyncio.run."""

    @wraps(func)
    def wrapper(*args, **kwargs):
        return asyncio.run(func(*args, **kwargs))

    return wrapper


@click.group()
@click.option(
    "--attempts",
    default=5,
    show_default=True,
    type=int,
    help="number of retry attempts for network requests",
)
@click.option(
    "--verbose",
    "-v",
    is_flag=True,
    help="enable verbose logging",
)
def webchain(attempts: int, verbose: bool):
    if os.environ.get("LOG_LEVEL"):
        log_level = logging._nameToLevel.get(os.environ.get("LOG_LEVEL", "").upper(), logging.INFO)
    else:
        log_level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(level=log_level, format="%(filename)s: %(message)s")

    if "WEBCHAIN_NETWORK_ATTEMPTS" not in os.environ:
        os.environ["WEBCHAIN_NETWORK_ATTEMPTS"] = str(attempts)

    pass


@webchain.command
@click.argument("url", required=True)
@click.option(
    "--robots-txt/--no-robots-txt",
    default=True,
)
@asyncio_click
async def tree(url: str, robots_txt: bool):
    try:
        crawled = await crawl(url, check_robots_txt=robots_txt)
    except Exception as e:
        print(f"error: {e}")
        sys.exit(1)

    print("")

    for node in crawled.nodes:
        line = "    " * node.depth + node.at

        if node.index_error:
            line += f" (not crawled: {type(node.index_error).__name__})"
        elif not node.indexed:
            line += " (not crawled)"

        if node.depth == 0:
            line += f" (limit={crawled.nominations_limit})"

        print(line)

    if any(node.unqualified for node in crawled.nodes):
        print("")
        for node in crawled.nodes:
            if node.unqualified:
                print(f"{len(node.unqualified)} unqualified in {node.at} -> {node.unqualified}")

    duration = datetime.fromisoformat(crawled.end) - datetime.fromisoformat(crawled.start)

    print(f"\ncrawled {len(crawled.nodes)} nodes in {duration.total_seconds():.2f} seconds")


@webchain.command
@click.argument("url", required=True)
@click.option(
    "--robots-txt/--no-robots-txt",
    default=True,
)
@asyncio_click
async def json(url: str, robots_txt: bool):
    try:
        crawled = await crawl(url, check_robots_txt=robots_txt)
    except Exception as e:
        print(f"error: {e}")
        sys.exit(1)

    serialized = serialize(crawled, indent="\t")
    print(serialized)


@webchain.command
@click.argument("path1", required=True, type=click.File())
@click.argument("path2", required=True, type=click.File())
def patch(path1: io.TextIOWrapper, path2: io.TextIOWrapper) -> None:
    try:
        res1 = deserialize(path1.read())
    except Exception as e:
        print(f"{path1.name} not valid crawl json: {e}")
        sys.exit(1)

    try:
        res2 = deserialize(path2.read())
    except Exception as e:
        print(f"{path2.name} not valid crawl json: {e}")
        sys.exit(1)

    patched_crawl = patch_state(res1, res2)

    if not patched_crawl:
        # no changes
        print("no changes detected")
        sys.exit(1)

    ret = serialize(patched_crawl, indent="\t")
    print(ret)


@webchain.command
@click.argument("file", required=True, type=click.File())
@click.option(
    "--robots-txt/--no-robots-txt",
    default=True,
)
@asyncio_click
async def enrich(file: io.TextIOWrapper, robots_txt: bool) -> None:
    try:
        webchain = deserialize(file.read())
    except Exception as e:
        print(f"error: {e}")
        sys.exit(1)

    enriched = await enrich_with_metadata(webchain, check_robots_txt=robots_txt)
    serialized = serialize(enriched, indent="\t")
    print(serialized)
