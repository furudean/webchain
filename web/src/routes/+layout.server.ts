import type { LayoutServerLoad } from "./$types"
import type { CrawledNode, DisplayNode } from "$lib/node"
import { string_to_color } from "$lib/color"
import tr46 from "tr46"

function create_display_node(node: CrawledNode, index: number): DisplayNode {
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
		last_updated: node.last_updated ? new Date(node.last_updated) : null
	}
}

function recent_nodes(nodes: DisplayNode[]): string[] {
	const newest_timestamp = Math.max(
		...nodes.map((n) => n.first_seen?.getTime() ?? 0)
	)
	if (!newest_timestamp) return []

	const now = new Date().getTime()
	const cohort_window = 1000 * 60 * 60 * 24 * 3.5 // 3.5 days
	const stale_threshold = 1000 * 60 * 60 * 24 * 14 // 14 days

	if (now - newest_timestamp > stale_threshold) {
		return []
	}

	return nodes
		.filter(
			(node) =>
				(node.first_seen?.getTime() ?? 0) > newest_timestamp - cohort_window
		)
		.map((n) => n.at)
}

export const load: LayoutServerLoad = async ({
	fetch
}): Promise<{
	nodes: DisplayNode[]
	recent_nodes: string[]
	nominations_limit: number | null
	start: Date | null
	end: Date | null
}> => {
	const [crawl_request, heartbeat_request] = await Promise.all([
		fetch("/crawler/current.json"),
		fetch("/crawler/heartbeat.json")
	])

	if (!crawl_request.ok || !crawl_request.ok) {
		throw new Error("Failed to fetch data")
	}

	try {
		const {
			nodes,
			nominations_limit
		}: {
			nodes: CrawledNode[]
			nominations_limit: number
			start: string
			end: string
		} = await crawl_request.json()
		const { start, end } = await heartbeat_request.json()
		const mapped_nodes = nodes.map(create_display_node)

		return {
			nodes: mapped_nodes,
			recent_nodes: recent_nodes(mapped_nodes),
			nominations_limit,
			start: new Date(start),
			end: new Date(end)
		}
	} catch (error) {
		console.error("Error parsing JSON:", error)
		return {
			nodes: [],
			recent_nodes: [],
			start: null,
			nominations_limit: null,
			end: null
		}
	}
}
