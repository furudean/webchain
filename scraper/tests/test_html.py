from scraper.html import get_node_nominations

def test_get_node_nominations_single():
    html = '''
    <html>
    <head>
        <link rel="webchain" href="https://chain.milkmedicine.net">
        <link rel="webchain-nomination" href="https://example.org">
    </head>
    </html>
    '''
    result = get_node_nominations(html, root="https://chain.milkmedicine.net")
    assert result == ["https://example.org"]
