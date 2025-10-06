from dataclasses import dataclass, field


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
    parent: str | None
    depth: int
    indexed: bool
    unqualified: list[str] = field(default_factory=list)
    """nominations that were already a part of the graph or exceeded the nominations limit"""
    first_seen: str | None = None
    last_updated: str | None = None
    html_metadata: HtmlMetadata | None = None


@dataclass
class CrawlResponse:
    nodes: list[CrawledNode]
    nominations_limit: int
    start: str
    end: str
