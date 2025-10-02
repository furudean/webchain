from dataclasses import dataclass


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


@dataclass
class HtmlMetadata:
    title: str | None
    description: str | None
    theme_color: str | None


@dataclass
class CrawledNodeWithMetadata(CrawledNode):
    html_metadata: HtmlMetadata | None = None


@dataclass
class CrawlResponse:
    nodes: list[CrawledNode] | list[CrawledNodeWithMetadata]
    nominations_limit: int
    start: str
    end: str
