import type { RequestHandler } from "./$types"
import { get_current_crawl } from '$lib/crawler'
import { html } from "common-tags"


export const GET: RequestHandler = async ({ fetch }) => {
	const crawl = await get_current_crawl(fetch)

	const feeds = crawl.nodes.flatMap(node => node.html_metadata?.syndication_feeds).filter(Boolean) as string[]

	const feed = html`
	<?xml version="1.0" encoding="utf-8"?>
	<opml version="2.0">
		<head>
			<title>mySubscriptions.opml</title>
			<dateCreated>Sat, 18 Jun 2005 12:11:52 GMT</dateCreated>
			<dateModified>Tue, 02 Aug 2005 21:42:48 GMT</dateModified>
			<ownerName>Dave Winer</ownerName>
			<ownerEmail>dave@scripting.com</ownerEmail>
		</head>
		<body>
			<outline text="CNET News.com"
			description="Tech news and business reports by CNET News.com. Focused on information technology, core topics include computers, hardware, software, networking, and Internet media."
			htmlUrl="http://news.com.com/"
			language="unknown"
			title="CNET News.com"
			type="rss"
			version="RSS2"
			xmlUrl="http://news.com.com/2547-1_3-0-5.xml"/>
		</body>
	</opml>
	`

	return new Response(feed, {
		status: 200,
		headers: {
			"Content-Type": "application/xml",
		}
	})
}
