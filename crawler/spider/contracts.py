from dataclasses import dataclass, field


@dataclass
class HtmlMetadata:
    title: str | None
    description: str | None
    theme_color: str | None


@dataclass
class CrawledNode:
    at: str
    parent: str | None
    children: list[str]
    """valid nominations"""
    depth: int
    indexed: bool
    index_error: Exception | None = None
    robots_ok: bool | None = None
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
