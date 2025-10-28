from spider.crawl import get_raw_nominations
from ordered_set import OrderedSet


async def test_get_node_nominations_single():
    html = """
    <html>
    <head>
        <link rel="webchain" href="https://mychain.net">
        <link rel="webchain-nomination" href="https://example.org">
    </head>
    </html>
    """
    result = get_raw_nominations(html, seed="https://mychain.net")
    assert OrderedSet(result or []) == OrderedSet(["https://example.org"])


async def test_get_node_nominations_multiple():
    html = """
    <html>
    <head>
        <link rel="webchain" href="https://mychain.net">
        <link rel="webchain-nomination" href="https://example.org">
        <link rel="webchain-nomination" href="https://example.com">
        <link rel="webchain-nomination" href="https://mysite.com">
    </head>
    </html>
    """
    result = get_raw_nominations(html, seed="https://mychain.net")
    assert OrderedSet(result or []) == OrderedSet(
        ["https://example.org", "https://example.com", "https://mysite.com"]
    )


async def test_get_node_nominations_missing():
    html = "<html></html>"
    result = get_raw_nominations(html, seed="https://mychain.net")
    assert result == OrderedSet([])


async def test_missing_webchain_tag():
    html = """
    <html>
    <head>
        <link rel="webchain-nomination" href="https://example.org">
        <link rel="webchain-nomination" href="https://example.com">
    </head>
    </html>
    """
    result = get_raw_nominations(html, seed="https://mychain.net")
    assert result == OrderedSet([])


async def test_different_webchain_tag():
    html = """
    <html>
    <head>
        <link rel="webchain" href="https://someotherchain.net">
        <link rel="webchain-nomination" href="https://example.org">
        <link rel="webchain-nomination" href="https://example.com">
    </head>
    </html>
    """
    result = get_raw_nominations(html, seed="https://mychain.net")
    assert result == OrderedSet([])


async def test_invalid_nomination_tag():
    html = """
    <html>
    <head>
        <link rel="webchain" href="https://mychain.net">
        <link rel="webchain-nomination" href="invalid-uri">
        <link rel="webchain-nomination" href="https://example.com">
    </head>
    </html>
    """
    result = get_raw_nominations(html, seed="https://mychain.net")
    assert OrderedSet(result or []) == OrderedSet(["https://example.com"])


async def test_mismatched_trailing_slash_on_seed():
    html = """
    <html>
    <head>
        <link rel="webchain" href="https://mychain.net/">
        <link rel="webchain-nomination" href="https://example.org">
    </head>
    </html>
    """

    result = get_raw_nominations(
        html,
        seed="https://mychain.net",  # note: no trailing slash
    )
    assert OrderedSet(result or []) == OrderedSet(["https://example.org"])


async def test_weird_permissive_case():
    html = """
    <html>
    <body>
        <div>
            <link rel="webchain" href="https://mychain.net">
            <link rel="webchain-nomination" href="https://example.org">
        </div>
    </body>
    </html>
    """
    result = get_raw_nominations(html, seed="https://mychain.net")
    assert OrderedSet(result or []) == OrderedSet(["https://example.org"])
