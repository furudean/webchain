from spider.metadata import get_html_metadata
from spider.contracts import HtmlMetadata


async def test_metadata():
    html = """
    <html>
    <head>
        <title>My Webchain Node</title>
        <meta name="description" content="This is my webchain node description.">
        <meta name="theme-color" content="#ccc">
    </head>
    </html>
    """

    result = get_html_metadata(html)
    assert result == HtmlMetadata(
        title="My Webchain Node",
        description="This is my webchain node description.",
        theme_color="#ccc",
    )


async def test_ignore_not_head():
    html = """
    <html>
    <body>
        <title>My Webchain Node</title>
        <meta name="description" content="This is my webchain node description.">
        <meta name="theme-color" content="#ccc">
    </body>
    </html>
    """

    result = get_html_metadata(html)
    assert result is None


async def test_metadata_og():
    html = """
    <html>
    <head>
        <meta property="og:title" content="title">
        <meta property="og:description" content="desc">
    </head>
    </html>
    """

    result = get_html_metadata(html)

    assert result == HtmlMetadata(
        title="title",
        description="desc",
        theme_color=None,
    )


async def test_metadata_twitter():
    html = """
    <html>
    <head>
        <meta name="twitter:title" content="twitter title">
        <meta name="twitter:description" content="twitter desc">
    </head>
    </html>
    """

    result = get_html_metadata(html)

    assert result == HtmlMetadata(
        title="twitter title",
        description="twitter desc",
        theme_color=None,
    )
