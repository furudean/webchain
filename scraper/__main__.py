import asyncio
import aiohttp

from scraper.html import get_node_nominations, load_page_html

ROOT = "https://chain-staging.milkmedicine.net"

async def recursively_print_nominations(
    url: str,
    session: aiohttp.ClientSession,
    depth: int = 0,
    is_last: bool = True,
    prefix: str = ""
):
    html = await load_page_html(url, session=session)
    nominations = await get_node_nominations(html, root=ROOT)

    if depth == 0:
        print(url)
    else:
        current_prefix = prefix + ("└─ " if is_last else "├─ ")
        print(f"{current_prefix}{url}")

    if nominations:
        for i, nomination in enumerate(nominations):
            is_last_child = i == len(nominations) - 1

            child_prefix = prefix + ("   " if is_last else "│  ") if depth > 0 else ""

            await recursively_print_nominations(
                nomination,
                session=session,
                depth=depth + 1,
                is_last=is_last_child,
                prefix=child_prefix
            )

async def main():
    async with aiohttp.ClientSession() as session:
        # print(ROOT)
        # html = await load_page_html(ROOT, session=session)
        # nominations = await get_node_nominations(html, root=ROOT)
        # print(nominations)

        await recursively_print_nominations(ROOT, session=session)

def run():
   asyncio.run(main())

if __name__ == "__main__":
    run()
