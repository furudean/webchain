from dataclasses import dataclass


@dataclass
class HtmlMetadata:
    title: str | None
    description: str | None
    theme_color: str | None


@dataclass
class CrawledNode:
    at: str
    children: list[str]
    """valid nominations"""
    references: list[str]
    """nominations that were already a part of the graph or exceeded the nominations limit"""
    parent: str | None
    depth: int
    indexed: bool
    first_seen: str | None = None
    last_updated: str | None = None
    html_metadata: HtmlMetadata | None = None


@dataclass
class CrawlResponse:
    nodes: list[CrawledNode]
    nominations_limit: int
    start: str
    end: str
