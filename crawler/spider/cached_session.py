import asyncio
import time
import logging
import os
import json
from typing import Optional, Dict, Any, Union
import re
from pathlib import Path

import aiohttp
import aiosqlite
from contextlib import asynccontextmanager
from typing import AsyncContextManager
import platformdirs

logger = logging.getLogger(__name__)
db_path = Path(
    os.environ.get(
        "WEBCHAIN_CACHE_DB",
        Path(platformdirs.user_cache_dir("webchain-spider", ensure_exists=True))
        / "http-cache.sqlite",
    )
)


logging.getLogger("aiosqlite").setLevel(logging.WARNING)  # noisy otherwise


def parse_cache_control(header: str) -> Dict[str, Optional[Union[int, bool]]]:
    """
    parse a Cache-Control header into a small dict
    """
    out: Dict[str, Optional[Union[int, bool]]] = {
        "no-store": False,
        "no-cache": False,
        "max-age": None,
    }
    if not header:
        return out

    # match directives like: token[= (token | "quoted string") ] , ...
    token_re = re.compile(
        r"\s*([!#$%&'\*+\-.\^_`|~0-9A-Za-z]+)(?:\s*=\s*(\"(?:[^\\\"]|\\.)*\"|[^,]*))?\s*(?:,|$)"
    )
    for m in token_re.finditer(header):
        name = m.group(1).lower()
        val = m.group(2)
        if val is None:
            if name == "no-store":
                out["no-store"] = True
            elif name == "no-cache":
                out["no-cache"] = True
            continue

        # strip optional quotes and surrounding whitespace
        val = val.strip()
        if val.startswith('"') and val.endswith('"') and len(val) >= 2:
            val = val[1:-1]

        if name == "max-age":
            try:
                out["max-age"] = int(val)
            except Exception:
                out["max-age"] = None
        elif name == "no-store":
            out["no-store"] = True
        elif name == "no-cache":
            out["no-cache"] = True

    return out


class CachedResponse:
    def __init__(self, status: int, headers: Dict[str, str], body: bytes, from_cache: bool = False):
        self.status = status
        self.headers = headers
        self.body = body
        self.from_cache = from_cache

    async def text(self, encoding: Optional[str] = None) -> str:
        if encoding is None:
            ct = self.headers.get("Content-Type", "")
            if "charset=" in ct:
                encoding = ct.split("charset=")[-1].strip()
            else:
                encoding = "utf-8"
        return self.body.decode(encoding, errors="replace")

    async def read(self) -> bytes:
        return self.body


class CachedClientSession:
    """
    drop-in replacement for aiohttp.ClientSession

    persists GET responses in sqlite, honoring Cache-Control and ETag headers
    """

    def __init__(self, *args, **kwargs):
        self.session = aiohttp.ClientSession(*args, **kwargs)
        self.db: Optional[aiosqlite.Connection] = None
        self.db_path = db_path
        self.lock = asyncio.Lock()

    async def ensure_db(self) -> None:
        if self.db is not None:
            return
        self.db = await aiosqlite.connect(self.db_path)
        await self.db.execute(
            """
            CREATE TABLE IF NOT EXISTS cache (
                url TEXT PRIMARY KEY,
                body BLOB,
                headers TEXT,
                etag TEXT,
                expiry REAL,
                cached_at REAL
            )
            """
        )
        await self.db.commit()
        logger.debug(f"using cache db at {self.db_path}")

    async def get_cached(self, url: str) -> Optional[Dict[str, Any]]:
        await self.ensure_db()
        async with self.db.execute(
            "SELECT body, headers, etag, expiry, cached_at FROM cache WHERE url = ?",
            (url,),
        ) as cur:
            row = await cur.fetchone()
            if not row:
                return None
            body, headers_json, etag, expiry, cached_at = row
            headers = json.loads(headers_json) if headers_json else {}
            return {
                "body": body,
                "headers": headers,
                "etag": etag,
                "expiry": expiry,
                "cached_at": cached_at,
            }

    async def save_cached(
        self,
        url: str,
        body: bytes,
        headers: Dict[str, str],
        etag: Optional[str],
        expiry: Optional[float],
    ) -> None:
        await self.ensure_db()
        headers_json = json.dumps(headers)
        cached_at = time.time()
        await self.db.execute(
            "INSERT OR REPLACE INTO cache (url, body, headers, etag, expiry, cached_at) VALUES (?, ?, ?, ?, ?, ?)",
            (url, body, headers_json, etag, expiry, cached_at),
        )
        await self.db.commit()

    async def delete_cached(self, url: str) -> None:
        await self.ensure_db()
        await self.db.execute("DELETE FROM cache WHERE url = ?", (url,))
        await self.db.commit()

    @asynccontextmanager
    async def get(self, url: str, **kwargs) -> AsyncContextManager[CachedResponse]:
        kwargs = dict(kwargs)
        headers = dict((kwargs.pop("headers") or {}) if kwargs.get("headers") is not None else {})

        async with self.lock:
            entry = await self.get_cached(url)

            # fresh cache hit: if max-age hasn't elapsed, serve the stored response
            # directly without hitting the network at all (RFC 9111 §4).
            if entry and entry["expiry"] is not None and time.time() < entry["expiry"]:
                logger.debug(f"cache hit: {url}")
                yield CachedResponse(200, entry["headers"], entry["body"], from_cache=True)
                return

            # conditional request: if the cached entry has a validator, attach it so
            # the server can reply with 304 instead of resending the full body.
            # prefer ETag (If-None-Match) over Last-Modified (If-Modified-Since) as
            # ETags are more precise (RFC 9110 §13.1).
            if entry and entry.get("etag"):
                headers.setdefault("If-None-Match", entry.get("etag"))
            elif entry and entry.get("headers", {}).get("Last-Modified"):
                headers.setdefault("If-Modified-Since", entry.get("headers").get("Last-Modified"))

        resp = await self.session.get(url, headers=headers, **kwargs)
        try:
            # 304 not modified: the server confirmed the cached copy is still current.
            # refresh the stored entry (updating expiry if a new max-age was given)
            # and return the cached body — no body was sent by the server.
            if resp.status == 304 and entry:
                resp_headers = {k: v for k, v in resp.headers.items()}
                cc = parse_cache_control(resp_headers.get("Cache-Control", ""))
                if cc.get("no-store"):
                    # server changed its mind — it no longer wants this response stored.
                    await self.delete_cached(url)
                else:
                    # only update/save cache if there are explicit caching headers.
                    # a 304 with no headers at all means the server gave us nothing to
                    # base a new expiry on, so leave the entry as-is.
                    has_cache_header = bool(
                        resp_headers.get("Cache-Control")
                        or resp_headers.get("ETag")
                        or entry.get("etag")
                        or entry.get("headers", {}).get("Last-Modified")
                    )
                    if has_cache_header:
                        expiry = None
                        if cc.get("max-age") is not None:
                            expiry = time.time() + int(cc["max-age"])
                        await self.save_cached(
                            url, entry["body"], entry["headers"], entry.get("etag"), expiry
                        )
                logger.debug(f"304 for {url}, returning cached body")
                yield CachedResponse(200, entry["headers"], entry["body"], from_cache=True)
                return

            # 2xx response: the server sent a fresh body.
            body = await resp.read()
            resp_headers = {k: v for k, v in resp.headers.items()}

            cc = parse_cache_control(resp_headers.get("Cache-Control", ""))
            etag = resp_headers.get("ETag")

            # compute expiry from max-age. without max-age we don't guess a TTL — the
            # entry will still be stored so we can send conditional requests next time,
            # but it will never be served from cache without revalidation.
            expiry: Optional[float]
            if cc.get("no-store"):
                expiry = None
            elif cc.get("max-age") is not None:
                expiry = time.time() + int(cc["max-age"])
            else:
                expiry = None

            # only cache responses that carry explicit caching headers (Cache-Control,
            # ETag, or Last-Modified). responses without any of these give us no
            # validator to reuse, so caching them would just waste disk space.
            has_cache_header = bool(
                resp_headers.get("Cache-Control")
                or resp_headers.get("ETag")
                or resp_headers.get("Last-Modified")
            )
            if resp.status >= 200 and resp.status < 300:
                async with self.lock:
                    if not cc.get("no-store") and has_cache_header:
                        await self.save_cached(url, body, resp_headers, etag, expiry)
                    elif entry:
                        # server previously sent caching headers but no longer does.
                        # drop the stale entry so we don't keep sending validators
                        # (e.g. If-None-Match) to a server that will ignore them.
                        await self.delete_cached(url)

            yield CachedResponse(resp.status, resp_headers, body)
        finally:
            await resp.release()

    async def close(self):
        await self.session.close()
        if self.db is not None:
            await self.db.close()

    async def __aenter__(self):
        await self.session.__aenter__()
        return self

    async def __aexit__(self, exc_type, exc, tb):
        await self.session.__aexit__(exc_type, exc, tb)
        if self.db is not None:
            await self.db.close()
