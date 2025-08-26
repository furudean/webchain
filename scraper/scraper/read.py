from scraper.crawl import crawl
from scraper.node import Node

async def recursively_read_nodes(url: str) -> None:
    def callback_wrapper(at: str, children: list[str], parent: str | None, depth: int) -> None:
        current_node = Node(at, parent, children)
        print(current_node.parent)

    await crawl(url, node_callback=callback_wrapper)
