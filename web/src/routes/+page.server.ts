import type { PageServerLoad } from "./$types"
import type { CrawledNode, DisplayNode } from "$lib/node"
import { string_to_color } from "$lib/color"
import tr46 from "tr46"

export const load: PageServerLoad = async ({
	fetch
}): Promise<{
	nodes: DisplayNode[]
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

		return {
			nodes: nodes.map((node, index): DisplayNode => {
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
			}),
			nominations_limit,
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
