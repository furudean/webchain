import aiohttp

from scraper.crawl import get_node_nominations
from scraper.http import load_page_html


async def recursively_print_nominations(
    url: str,
    session: aiohttp.ClientSession,
    root: str | None = None,
    seen: set[str] | None = None,
    depth: int = 0,
    is_last: bool = True,
    prefix: str = '',
):
    if root is None:
        root = url

    if seen is None:
        seen = set()

    seen.add(url)

    if depth == 0:
        print(url)
    else:
        print(prefix + ('└─ ' if is_last else '├─ ') + url)

    html = await load_page_html(url, session=session)

    if html is None:
        # could not load page, stop recursion here
        return

    nominations = get_node_nominations(html=html, root=root)

    if nominations:
        for i, nomination in enumerate(nominations or []):
            child_prefix = prefix + ('   ' if is_last else '│  ') if depth > 0 else ''

            if nomination in seen:
                continue

            seen.add(nomination)

            await recursively_print_nominations(
                nomination,
                session=session,
                root=root,
                seen=seen,
                depth=depth + 1,
                is_last=i == len(nominations) - 1,
                prefix=child_prefix,
            )
