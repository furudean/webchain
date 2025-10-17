import dataclasses
import json

from spider.crawl import CrawlResponse, CrawledNode


def safe_asdict(obj):
    """Recursively convert dataclass to dict, converting non-serializable fields to string."""
    if dataclasses.is_dataclass(obj):
        result = {}
        for field in dataclasses.fields(obj):
            value = getattr(obj, field.name)
            result[field.name] = safe_asdict(value)
        return result
    elif isinstance(obj, (list, tuple)):
        return [safe_asdict(item) for item in obj]
    elif isinstance(obj, dict):
        return {k: safe_asdict(v) for k, v in obj.items()}
    else:
        try:
            json.dumps(obj)
            return obj
        except TypeError:
            return str(obj)


def serialize(crawled: CrawlResponse, **kwargs) -> str:
    data = safe_asdict(crawled)
    return json.dumps(data, **kwargs)


def deserialize(data: str) -> CrawlResponse:
    obj = json.loads(data)
    allowed_fields = {field.name for field in dataclasses.fields(CrawledNode)}
    nodes = [
        CrawledNode(**{k: v for k, v in node.items() if k in allowed_fields})
        for node in obj["nodes"]
    ]

    return CrawlResponse(
        nodes=nodes,
        nominations_limit=obj["nominations_limit"],
        start=obj["start"],
        end=obj["end"],
    )
