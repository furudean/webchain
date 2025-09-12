from scraper.crawl import crawl, CrawledNode
from scraper.node import Node
from scraper.hash import HashTable
from datetime import datetime, timezone
import time

async def read_chain_into_table(root: str) -> HashTable:
    T = HashTable()

    crawled = await crawl(root)
    saved_nodes = []
    for i in crawled.nodes:
        saved_nodes.append(CrawledNodeToNode(i))

    for i in saved_nodes:
        T.insert(i)
    return T

def CrawledNodeToNode(to_convert: CrawledNode) -> Node:
    # print(f"url: {to_convert.at} parent: {to_convert.parent} children: {to_convert.children}")
    # TO DO : use Node.addChild instead of direct assignment
    return Node(to_convert.at, to_convert.parent, to_convert.children, to_convert.indexed)
