import type { RequestHandler } from "./$types"
import { get_current_crawl } from '$lib/crawler'
import type { CrawledNode } from "$lib/node"
import format_xml from 'xml-formatter';
import { nice_url } from "$lib/url";

function node_to_outline(node: CrawledNode): string | undefined {
	const label = nice_url(node.at)

	const many = node.syndication_feeds?.length > 1

	const outlines = node.syndication_feeds?.map(
		(feed) => `
			<outline text="${many ? (feed.title || feed.url) : label}"
				title="${feed.title}"
				description="${feed.description}"
				xmlUrl="${feed.url}"
				type="rss"
				version="${feed.version}"
				${feed.published ? `created="${new Date(feed.published).toUTCString()}"` : ''}
				htmlUrl="${node.at}" />
			`
	).join('\n')

	if (many) {
		return `<outline text="${label}">${outlines}</outline>`
	} else {
		return outlines
	}
}


export const GET: RequestHandler = async ({ fetch, url }) => {
	const crawl = await get_current_crawl(fetch)


	const feed = format_xml(`
	<?xml version="1.0" encoding="utf-8"?>
	<opml version="2.0">
		<head>
			<title>milkmedicine webchain member feeds</title>
			<dateCreated>${new Date().toUTCString()}</dateCreated>
			<dateModified>${new Date(crawl.end).toUTCString()}</dateModified>
			<ownerId>${new URL('/', url).href}</ownerId>
			<ownerName>Webchain Admin</ownerName>
			<ownerEmail>meri@himawari.fun</ownerEmail>
			<docs>https://opml.org/spec2.opml</docs>
		</head>
		<body>
			${crawl.nodes.map(node_to_outline).join('\n')}
		</body>
	</opml>
	`)

	return new Response(feed, {
		status: 200,
		headers: {
			"Content-Type": "text/xml+opml",
			// "Content-Disposition": 'attachment; filename="milkmedicine webchain member feeds.opml"'
		}
	})
}
