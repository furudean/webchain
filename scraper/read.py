import aiohttp
from scraper.node import Node
from scraper.crawl import get_node_nominations, load_page_html

chain = []

async def read_chain(
    url: str,
    session: aiohttp.ClientSession,
    root: str | None = None,
    last: str | None = None,
    seen: set[str] | None = None,
    depth: int = 0,
):
    if root is None:
        root = url

    if depth == 0:
        url = root

    if seen is None:
        seen = set()

    seen.add(url)
    current_node = Node(url)
    print(f"depth:{depth}")
    print(f"at : [ {current_node} ]")
    print(f"last: {last}")

    # if depth == 0:
    #     chain.append(Node.root(url))
    # else:
    #     chain.append(Node.leaf(url))


    html = await load_page_html(url, session=session)

    if html is None:
        # could not load page, stop recursion here
        return

    nominations = await get_node_nominations(html=html, root=root)


    if nominations:
        for i, nomination in enumerate(nominations or []):
            if nomination in seen:
                continue

            seen.add(nomination)
            # current_node.addChild(nomination)
            print(f"nom {i} of [{url}] : [{nomination}] ")
            # print(f"nom at : [ {current_node} ]")
            print(f"last at nom: [ {last}]")
            print(f"---------------")

            await read_chain(
                nomination,
                session=session,
                root=root,
                last=url,
                seen=seen,
                depth=depth + 1,
            )
