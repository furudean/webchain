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
    nodes = [CrawledNode(**node) for node in obj['nodes']]

    return CrawlResponse(
        nodes=nodes,
        nominations_limit=obj['nominations_limit'],
        start=obj['start'],
        end=obj['end'],
    )
