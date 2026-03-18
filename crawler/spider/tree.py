import asyncio
from datetime import datetime
import os
import queue
import threading
import urwid

from spider.crawl import crawl
from spider.contracts import CrawledNode


_PALETTE = [
    ("dim", "dark gray", "default"),
    ("error", "light red", "default"),
    ("unqualified", "yellow", "default"),
]


class TreeCrawlUI:
    def __init__(self, url: str, robots_txt: bool, exit_when_done: bool = False) -> None:
        self.url = url
        self.robots_txt = robots_txt
        self.exit_when_done = exit_when_done
        self._widgets: dict[str, urwid.Text] = {}
        self._content: dict[str, list] = {}
        self._depth: dict[str, int] = {}
        self._parent: dict[str, str | None] = {}
        self._children: dict[str, list[str]] = {}
        self._cached: set[str] = set()
        self._inflight: list[str] = []
        self.result = None
        self.error: Exception | None = None

        self._walker = urwid.SimpleFocusListWalker([])
        self._status = urwid.Text("crawling...")
        self._queue: queue.SimpleQueue = queue.SimpleQueue()
        self._pipe_write: int | None = None
        self._main_loop: urwid.MainLoop | None = None

    def _make_unqualified_prefix(self, at: str) -> str:
        """Indentation for unqualified items shown as children of `at`, without arm."""
        path: list[str] = []
        cur = at
        while self._depth.get(cur, 0) > 0:
            path.append(cur)
            cur = self._parent.get(cur) or ""
        path.reverse()
        prefix = ""
        for node in path:
            prefix += "    " if self._is_last(node) else "│   "
        prefix += "    "
        return prefix

    def _is_last(self, at: str) -> bool:
        siblings = self._children.get(self._parent.get(at) or "", [])
        return bool(siblings) and siblings[-1] == at

    def _make_prefix(self, at: str) -> str:
        if self._depth.get(at, 0) == 0:
            return ""
        path: list[str] = []
        cur = at
        while self._depth.get(cur, 0) > 0:
            path.append(cur)
            cur = self._parent.get(cur) or ""
        path.reverse()
        prefix = ""
        for ancestor in path[:-1]:
            prefix += "    " if self._is_last(ancestor) else "│   "
        prefix += "└── " if self._is_last(at) else "├── "
        return prefix

    def _subtree_size(self, at: str) -> int:
        if at not in self._widgets:
            return 0
        return 1 + sum(self._subtree_size(c) for c in self._children.get(at, []))

    def _redraw(self, at: str) -> None:
        w = self._widgets.get(at)
        if w is None:
            return
        prefix = self._make_prefix(at)
        content = self._content.get(at, [at])
        markup = ([("dim", prefix)] if prefix else []) + content
        w.set_text(markup)
        for child in self._children.get(at, []):
            self._redraw(child)

    def _enqueue(self, fn) -> None:
        if self._pipe_write is not None:
            self._queue.put(fn)
            try:
                os.write(self._pipe_write, b"\x00")
            except OSError:
                pass
        else:
            fn()

    def _flush_queue(self, _data: bytes) -> None:
        while not self._queue.empty():
            try:
                self._queue.get_nowait()()
            except queue.Empty:
                break

    def _handle_input(self, key: str) -> None:
        if key in ("q", "Q"):
            raise urwid.ExitMainLoop()

    def run(self) -> None:
        self._main_loop = urwid.MainLoop(
            urwid.Frame(
                body=urwid.ScrollBar(urwid.ListBox(self._walker)),
                footer=urwid.Pile([urwid.Divider("─"), self._status]),
            ),
            palette=_PALETTE,
            unhandled_input=self._handle_input,
        )
        self._pipe_write = self._main_loop.watch_pipe(self._flush_queue)
        threading.Thread(target=lambda: asyncio.run(self._crawl()), daemon=True).start()
        self._main_loop.run()

    async def _crawl(self) -> None:
        max_attempts = os.environ.get("WEBCHAIN_NETWORK_ATTEMPTS", "5")

        def _update_status() -> None:
            self._status.set_text("crawling... " + " ".join(self._inflight))

        def on_node_start(at: str, parent: str | None, depth: int) -> None:
            def _update() -> None:
                self._parent[at] = parent
                self._depth[at] = depth
                existing = self._children.get(parent or "", [])
                prev_last = existing[-1] if existing else None

                if parent and parent in self._widgets:
                    parent_idx = self._walker.index(self._widgets[parent])
                    offset = sum(self._subtree_size(c) for c in existing)
                    insert_pos = parent_idx + 1 + offset
                else:
                    insert_pos = len(self._walker)

                self._children.setdefault(parent or "", []).append(at)
                self._content[at] = [("dim", at)]
                w = urwid.Text("")
                self._widgets[at] = w
                self._walker.insert(insert_pos, w)
                self._redraw(at)
                if prev_last:
                    self._redraw(prev_last)
                self._inflight.append(at)
                _update_status()

            self._enqueue(_update)

        def on_cache_hit(url: str) -> None:
            self._enqueue(lambda: self._cached.add(url.rstrip("/")))

        def on_node_complete(node: CrawledNode, nominations_limit: int) -> None:
            def _update() -> None:
                if node.at not in self._widgets:
                    return
                parts: list = [node.at]
                if node.depth == 0:
                    parts.append(("dim", f" (limit={nominations_limit})"))
                if node.at in self._cached:
                    parts.append(("dim", " (cached)"))
                elif node.fetch_duration is not None and node.fetch_duration > 3:
                    parts.append(("dim", f" (took {node.fetch_duration:.1f}s)"))
                if node.index_error:
                    parts.append(("error", f" (not crawled: {type(node.index_error).__name__})"))
                self._content[node.at] = parts
                self._redraw(node.at)
                if node.unqualified:
                    prefix = self._make_unqualified_prefix(node.at)
                    node_idx = self._walker.index(self._widgets[node.at])
                    insert_pos = node_idx + self._subtree_size(node.at)
                    for url in node.unqualified:
                        w = urwid.Text([("dim", prefix), ("unqualified", "unqualified "), url])
                        self._walker.insert(insert_pos, w)
                        insert_pos += 1
                if node.at in self._inflight:
                    self._inflight.remove(node.at)
                _update_status()

            self._enqueue(_update)

        def on_retry(url: str, attempt: int) -> None:
            at = url.rstrip("/")

            def _update() -> None:
                if at not in self._widgets:
                    return
                self._content[at] = [("dim", at), ("dim", f" (attempt {attempt}/{max_attempts})")]
                self._redraw(at)

            self._enqueue(_update)

        try:
            self.result = await crawl(
                self.url,
                check_robots_txt=self.robots_txt,
                on_node_start=on_node_start,
                on_node_complete=on_node_complete,
                on_retry=on_retry,
                on_cache_hit=on_cache_hit,
            )
        except Exception as e:
            self.error = e
            msg = f"error: {e} — q to quit"
            self._enqueue(lambda: self._status.set_text(("error", msg)))
            return

        duration = datetime.fromisoformat(self.result.end) - datetime.fromisoformat(
            self.result.start
        )
        summary = (
            f"crawled {len(self.result.nodes)} nodes in {duration.total_seconds():.2f}s — q to quit"
        )

        def _done() -> None:
            if self.exit_when_done:
                raise urwid.ExitMainLoop()
            self._status.set_text(summary)

        self._enqueue(_done)


def print_tree(ui: TreeCrawlUI) -> None:
    for w in ui._walker:
        text, _ = w.get_text()
        print(text if isinstance(text, str) else text.decode())
