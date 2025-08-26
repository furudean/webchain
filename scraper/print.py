from scraper.crawl import crawl


async def recursively_print_nominations(url: str) -> None:
    def callback_wrapper(at: str, children: list[str], parent: str, depth: int) -> None:
        print('    ' * depth + at)

    await crawl(url, node_callback=callback_wrapper)
