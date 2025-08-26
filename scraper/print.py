from scraper.crawl import crawl


async def recursively_print_nominations(url: str) -> None:
    def callback_wrapper(url: str, depth: int, is_last: bool) -> None:
        if depth == 0:
            print(url)
        else:
            prefix = '│   ' * (depth - 1) + ('└─ ' if is_last else '├─ ')
            print(prefix + url)

    await crawl(url, node_callback=callback_wrapper)
