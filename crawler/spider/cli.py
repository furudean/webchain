import asyncio
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
from spider.tree import TreeCrawlUI, print_tree


def asyncio_click(func):
    """Decorator that wraps coroutine with asyncio.run."""

    @wraps(func)
    def wrapper(*args, **kwargs):
        return asyncio.run(func(*args, **kwargs))

    return wrapper


def common_options(func):
    @click.option("--verbose", "-v", is_flag=True, default=False, help="enable verbose logging")
    @wraps(func)
    def wrapper(*args, verbose: bool, **kwargs):
        if verbose:
            logging.getLogger().setLevel(logging.DEBUG)
        return func(*args, **kwargs)

    return wrapper


def network_options(func):
    @click.option(
        "--attempts", default=5, show_default=True, type=int, help="number of retry attempts"
    )
    @click.option(
        "--no-cache", is_flag=True, default=False, help="disable disk cache from previous requests"
    )
    @click.option(
        "--v4", is_flag=True, default=False, help="only use ipv4, even if ipv6 is available"
    )
    @click.option(
        "--robots-txt/--no-robots-txt", default=True, help="respect robots.txt files... or don't!"
    )
    @wraps(func)
    def wrapper(*args, attempts: int, no_cache: bool, v4: bool, **kwargs):
        if "WEBCHAIN_NETWORK_ATTEMPTS" not in os.environ:
            os.environ["WEBCHAIN_NETWORK_ATTEMPTS"] = str(attempts)
        if no_cache:
            os.environ["WEBCHAIN_NO_CACHE"] = "1"
        if v4:
            os.environ["WEBCHAIN_IPV4"] = "1"
        return func(*args, **kwargs)

    return wrapper


@click.group()
def webchain():
    log_level = logging._nameToLevel.get(os.environ.get("LOG_LEVEL", "").upper(), logging.INFO)
    logging.basicConfig(level=log_level, format="%(filename)s: %(message)s")


@webchain.command
@click.argument("url", required=True)
@click.option(
    "--print",
    "print_output",
    is_flag=True,
    default=False,
    help="print tree to stdout instead of paging",
)
@common_options
@network_options
def tree(url: str, robots_txt: bool, print_output: bool):
    logging.getLogger().setLevel(logging.WARNING)

    ui = TreeCrawlUI(url, robots_txt, exit_when_done=print_output)
    ui.run()

    if ui.error:
        print(f"error: {ui.error}")
        sys.exit(1)

    if print_output:
        print_tree(ui)


@webchain.command
@click.argument("url", required=True)
@common_options
@network_options
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
@common_options
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
@common_options
@network_options
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
