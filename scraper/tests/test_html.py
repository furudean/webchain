from scraper.html import get_node_nominations


async def test_get_node_nominations_single():
    html = """
    <html>
    <head>
        <link rel="webchain" href="https://mychain.net">
        <link rel="webchain-nomination" href="https://example.org">
    </head>
    </html>
    """
    result = await get_node_nominations(html, root='https://mychain.net')
    assert result == ['https://example.org']


async def test_get_node_nominations_two():
    html = """
    <html>
    <head>
        <link rel="webchain" href="https://mychain.net">
        <link rel="webchain-nomination" href="https://example.org">
        <link rel="webchain-nomination" href="https://example.com">
    </head>
    </html>
    """
    result = await get_node_nominations(html, root='https://mychain.net')
    assert result == ['https://example.org', 'https://example.com']


async def test_get_node_nominations_three():
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
    result = await get_node_nominations(html, root='https://mychain.net')
    assert result == ['https://example.org', 'https://example.com']


async def test_get_node_nominations_none():
    html = '<html></html>'
    result = await get_node_nominations(html, root='https://mychain.net')
    assert result == None


async def test_missing_webchain_tag():
    html = """
    <html>
    <head>
        <link rel="webchain-nomination" href="https://example.org">
        <link rel="webchain-nomination" href="https://example.com">
    </head>
    </html>
    """
    result = await get_node_nominations(html, root='https://mychain.net')
    assert result == None


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
    result = await get_node_nominations(html, root='https://mychain.net')
    assert result == None


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
    result = await get_node_nominations(html, root='https://mychain.net')
    assert result == ['https://example.com']
