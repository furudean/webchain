import type { LayoutServerLoad } from "./$types"
import type { CrawledNode, CrawlResponse, DisplayNode } from "$lib/node"
import { string_to_color } from "$lib/color"
import tr46 from "tr46"

function create_display_node(
	node: CrawledNode,
	index: number,
	is_recent: boolean
): DisplayNode {
	const url = new URL(node.at)
	const label =
		tr46.toUnicode(url.hostname.replace(/^www\./i, "")).domain +
		url.pathname.replace(/\/$/, "")

	return {
		...node,
		index,
		generated_color:
			node.html_metadata?.theme_color || string_to_color(node.at),
		url,
		label,
		url_param: url.hostname + url.pathname.replace(/\/$/, ""),
		first_seen: node.first_seen ? new Date(node.first_seen) : null,
		last_updated: node.last_updated ? new Date(node.last_updated) : null,
		is_recent: is_recent
	}
}

function recent_nodes(nodes: CrawledNode[]): Set<string> {
	const newest_timestamp = Math.max(
		...nodes.map((n) => (n?.first_seen ? new Date(n.first_seen).getTime() : 0))
	)
	if (!newest_timestamp) return new Set()

	const now = new Date().getTime()
	const cohort_window = 1000 * 60 * 60 * 24 * 3.5 // 3.5 days
	const stale_threshold = 1000 * 60 * 60 * 24 * 14 // 14 days

	if (now - newest_timestamp > stale_threshold) {
		return new Set()
	}

	return new Set(
		nodes
			.filter(
				(node) =>
					(node?.first_seen ? new Date(node.first_seen).getTime() : 0) >
					newest_timestamp - cohort_window
			)
			.map((n) => n.at)
	)
}

let last_crawl: CrawlResponse | undefined = undefined
let last_crawl_etag: string | null = null

export const load: LayoutServerLoad = async ({
	fetch
}): Promise<{
	nodes: DisplayNode[]
	nominations_limit: number | null
	start: Date | null
	end: Date | null
}> => {
	const headers = new Headers()

	if (last_crawl_etag) headers.append('if-none-match', last_crawl_etag)

	const [crawl_request, heartbeat_request] = await Promise.all([
		fetch("/crawler/current.json", { headers }),
		fetch("/crawler/heartbeat.json")
	])

	let crawl_response: CrawlResponse | undefined = undefined

	if (crawl_request.status === 304 && last_crawl) {
		crawl_response = last_crawl
	} else if (crawl_request.ok) {
		last_crawl_etag = crawl_request.headers.get('etag')
		crawl_response = (await crawl_request.json()) as CrawlResponse
		last_crawl = crawl_response
	} else {
		throw new Error("failed to fetch /crawler/current.json")
	}

	if (!heartbeat_request.ok) {
		throw new Error("failed to fetch /crawler/heartbeat.json")
	}

	const nodes = crawl_response.nodes

	try {
		const { start, end } = await heartbeat_request.json()
		const recent = recent_nodes(nodes)
		const mapped_nodes = nodes.map((node, i) =>
			create_display_node(node, i, recent.has(node.at))
		)

		return {
			nodes: mapped_nodes,
			nominations_limit: crawl_response.nominations_limit,
			start: new Date(start),
			end: new Date(end)
		}
	} catch (error) {
		console.error("Error parsing JSON:", error)
		return {
			nodes: [],
			start: null,
			nominations_limit: null,
			end: null
		}
	}
}
