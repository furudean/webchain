import dataclasses
import json

from scraper.crawl import CrawlResponse, CrawledNode


def serialize(crawled: CrawlResponse, **kwargs) -> str:
    data = {
        'nodes': [dataclasses.asdict(node) for node in crawled.nodes],
        'nominations_limit': crawled.nominations_limit,
        'start': crawled.start,
        'end': crawled.end,
    }
    return json.dumps(data, **kwargs)


def deserialize(data: str) -> CrawlResponse:
    obj = json.loads(data)
    nodes = []
    for node in obj['nodes']:
        # Only pass arguments that exist in CrawledNode's __init__
        valid_keys = {field.name for field in dataclasses.fields(CrawledNode)}
        filtered_node = {k: v for k, v in node.items() if k in valid_keys}
        nodes.append(CrawledNode(**filtered_node))

    return CrawlResponse(
        nodes=nodes,
        nominations_limit=obj.get('nominations_limit'),
        start=obj.get('start'),
        end=obj.get('end'),
    )
