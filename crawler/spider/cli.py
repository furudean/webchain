import asyncio
from datetime import datetime
import io
import os
import sys
from functools import wraps
import logging
import click
from rich.live import Live
from rich.tree import Tree as RichTree
from rich.text import Text

from spider.crawl import crawl
from spider.contracts import CrawledNode
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
@click.option(
    "--no-cache",
    is_flag=True,
    help="disable disk cache for http requests",
)
@click.option(
    "--v4",
    is_flag=True,
    help="only use ipv4 when making reequests (disables happy eyeballs / ipv6)",
)
def webchain(attempts: int, verbose: bool, no_cache: bool, v4: bool):
    if os.environ.get("LOG_LEVEL"):
        log_level = logging._nameToLevel.get(os.environ.get("LOG_LEVEL", "").upper(), logging.INFO)
    else:
        log_level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(level=log_level, format="%(filename)s: %(message)s")

    if "WEBCHAIN_NETWORK_ATTEMPTS" not in os.environ:
        os.environ["WEBCHAIN_NETWORK_ATTEMPTS"] = str(attempts)

    if no_cache:
        os.environ["WEBCHAIN_NO_CACHE"] = "1"

    if v4:
        os.environ["WEBCHAIN_IPV4"] = "1"

    pass


@webchain.command
@click.argument("url", required=True)
@click.option(
    "--robots-txt/--no-robots-txt",
    default=True,
)
@asyncio_click
async def tree(url: str, robots_txt: bool):
    logging.getLogger().setLevel(logging.WARNING)

    max_attempts = os.environ["WEBCHAIN_NETWORK_ATTEMPTS"]

    rich_nodes: dict[str, RichTree] = {}
    labels: dict[str, Text] = {}
    cached_urls: set[str] = set()
    root_rich: RichTree | None = None

    live = Live(refresh_per_second=10)

    def on_node_start(at: str, parent: str | None, depth: int) -> None:
        nonlocal root_rich
        label = Text(at, style="dim")
        labels[at] = label
        if depth == 0:
            root_rich = RichTree(label, guide_style="dim")
            rich_nodes[at] = root_rich
            live.update(root_rich)
        elif parent and parent in rich_nodes:
            branch = rich_nodes[parent].add(label)
            rich_nodes[at] = branch

    def on_cache_hit(cache_url: str) -> None:
        cached_urls.add(cache_url.rstrip("/"))

    def on_node_complete(node: CrawledNode, nominations_limit: int) -> None:
        label = labels.get(node.at)
        if label is None:
            return
        label.plain = node.at
        label.style = ""
        if node.depth == 0:
            label.append(f" (limit={nominations_limit})", style="dim")
        if node.at in cached_urls:
            label.append(" (cached)", style="dim")
        elif node.fetch_duration is not None and node.fetch_duration > 3:
            label.append(f" (took {node.fetch_duration:.1f}s)", style="dim")
        if node.index_error:
            label.append(f" (not crawled: {type(node.index_error).__name__})", style="red")

    def on_retry(retry_url: str, attempt: int) -> None:
        at = retry_url.rstrip("/")
        label = labels.get(at)
        if label is None:
            return
        label.plain = at
        label.append(f" (attempt {attempt}/{max_attempts})", style="dim")

    with live:
        try:
            crawled = await crawl(
                url,
                check_robots_txt=robots_txt,
                on_node_start=on_node_start,
                on_node_complete=on_node_complete,
                on_retry=on_retry,
                on_cache_hit=on_cache_hit,
            )
        except Exception as e:
            live.console.print(f"error: {e}")
            sys.exit(1)

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
