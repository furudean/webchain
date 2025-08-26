from scraper.crawl import crawl


async def recursively_print_nominations(url: str) -> None:
    def callback_wrapper(at: str, children: list[str], parent: str | None, depth: int) -> None:
        print('    ' * depth + at)
        # print(f"depth: {depth} at: [{at}]")
        # print(f"parent: {[parent]}")
        # print(f"children: {children}")
        # print("----------------------")

    await crawl(url, node_callback=callback_wrapper)
