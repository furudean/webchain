import xml_format from "xml-formatter"
import type { RequestHandler } from "./$types"
import { get_current_crawl } from "$lib/crawler"
import type { CrawledNode } from "$lib/node"
import { nice_url } from "$lib/url"
import xmle from "xml-escape"

function build_entry(node: CrawledNode, base_url: string): string {
	const qs = new URLSearchParams()
	qs.append("url", node.at)
	const snap_url = new URL("/api/snap?" + qs, base_url).href

	const label = nice_url(node.at)
	const meta_title = node.html_metadata?.title
	const title =
		meta_title && meta_title !== label ? `${meta_title} — ${label}` : label

	return `
		<item>
			<title>${xmle(title)}</title>
			<link>${node.at}</link>
			<guid isPermaLink="true">${node.at}</guid>
			${node.html_metadata?.description ? `<description>${xmle(node.html_metadata.description)}</description>` : ""}
			<pubDate>${new Date(node.first_seen ?? 0).toUTCString()}</pubDate>
			<lastBuildDate>${new Date(node.last_updated ?? 0).toUTCString()}</lastBuildDate>
			<enclosure url="${snap_url}" type="image/webp" />
		</item>`
}

export const GET: RequestHandler = async ({ fetch, url }) => {
	const crawl = await get_current_crawl(fetch)
	const base_url = new URL("/", url).href

	const entries = crawl.nodes
		.toSorted(
			(a, b) =>
				new Date(a.first_seen || 0).getTime() -
				new Date(b.first_seen || 0).getTime()
		)
		.map((node) => build_entry(node, base_url))

	const xml = `<?xml version="1.0" encoding="UTF-8" ?>
		<rss version="2.0">
			<channel>
				<title>milkmedicine member sites</title>
				<link>${base_url}</link>
				<description>feed of milkmedicine webchain member sites</description>
				<image>
					<url>${new URL("/favicon.png", base_url)}</url>
					<title>milkmedicine's logo</title>
					<link>${base_url}</link>
				</image>
				<pubDate>Sun, 01 Feb 2026 02:58:20 GMT</pubDate>
				<lastBuildDate>${new Date(crawl.end).toUTCString()}</lastBuildDate>
				${entries.join("\n")}
			</channel>
		</rss>`

	console.log(xml)

	return new Response(xml_format(xml, { collapseContent: true }), {
		status: 200,
		headers: {
			"Content-Type": "application/rss+xml"
		}
	})
}
