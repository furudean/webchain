from scraper.crawl import crawl


async def recursively_print_nominations(url: str) -> None:
    def callback_wrapper(url: str, parent: str, depth: int) -> None:
        print("    " * (depth + 1) + url)

    print(url)

    await crawl(url, node_callback=callback_wrapper)
