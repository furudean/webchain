from dataclasses import dataclass, field
from typing import Protocol


@dataclass
class HtmlMetadata:
    title: str | None
    description: str | None
    theme_color: str | None


@dataclass
class SyndicationFeed:
    url: str
    title: str | None = None
    description: str | None = None
    published: str | None = None
    updated: str | None = None
    version: str | None = None


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
    fetch_duration: float | None = None
    first_seen: str | None = None
    last_updated: str | None = None
    html_metadata: HtmlMetadata | None = None
    syndication_feeds: list[SyndicationFeed] = field(default_factory=list)


class OnNodeStart(Protocol):
    def __call__(self, at: str, parent: str | None, depth: int) -> None: ...


class OnNodeComplete(Protocol):
    def __call__(self, node: "CrawledNode", nominations_limit: int) -> None: ...


class OnRetry(Protocol):
    def __call__(self, url: str, attempt: int) -> None: ...


class OnCacheHit(Protocol):
    def __call__(self, url: str) -> None: ...


@dataclass
class CrawlResponse:
    nodes: list[CrawledNode]
    nominations_limit: int
    start: str
    end: str
