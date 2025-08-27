from scraper.crawl import get_node_nominations


async def test_get_node_nominations_single():
    html = """
    <html>
    <head>
        <link rel="webchain" href="https://mychain.net">
        <link rel="webchain-nomination" href="https://example.org">
    </head>
    </html>
    """
    result = get_node_nominations(html, root='https://mychain.net')
    assert result == ['https://example.org']


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
    result = get_node_nominations(html, root='https://mychain.net')
    assert result == ['https://example.org', 'https://example.com', 'https://mysite.com']


async def test_get_node_nominations_missing():
    html = '<html></html>'
    result = get_node_nominations(html, root='https://mychain.net')
    assert result is None


async def test_missing_webchain_tag():
    html = """
    <html>
    <head>
        <link rel="webchain-nomination" href="https://example.org">
        <link rel="webchain-nomination" href="https://example.com">
    </head>
    </html>
    """
    result = get_node_nominations(html, root='https://mychain.net')
    assert result is None


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
    result = get_node_nominations(html, root='https://mychain.net')
    assert result is None


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
    result = get_node_nominations(html, root='https://mychain.net')
    assert result == ['https://example.com']


async def test_ignore_seen():
    html = """
    <html>
    <head>
        <link rel="webchain" href="https://mychain.net">
        <link rel="webchain-nomination" href="https://example.com">
        <link rel="webchain-nomination" href="https://example.org">
    </head>
    </html>
    """

    seen = {'https://example.com'}
    result = get_node_nominations(html, root='https://mychain.net', seen=seen)
    assert result == ['https://example.org']


async def test_mismatched_trailing_slash_on_root():
    html = """
    <html>
    <head>
        <link rel="webchain" href="https://mychain.net/">
        <link rel="webchain-nomination" href="https://example.org">
    </head>
    </html>
    """

    seen = {'https://example.com'}
    result = get_node_nominations(
        html,
        root='https://mychain.net',  # note: no trailing slash
        seen=seen,
    )
    assert result == ['https://example.org']
