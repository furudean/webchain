import type { PageServerLoad } from "./$types"
import type { CrawledNode, Node } from "$lib/node"
import { string_to_color } from "$lib/color"

export const load: PageServerLoad = async ({
	fetch
}): Promise<{
	nodes: Node[]
	nominations_limit: number | null
	start: Date | null
	end: Date | null
}> => {
	const request = await fetch("/crawler/data.json")

	if (!request.ok) {
		throw new Error("Failed to fetch data")
	}

	try {
		const {
			nodes,
			nominations_limit,
			start,
			end
		}: {
			nodes: CrawledNode[]
			nominations_limit: number
			start: string
			end: string
		} = await request.json()

		const no_www = /^www\./i

		return {
			nodes: nodes.map((node) => ({
				...node,
				generated_color: node.indexed
					? node.html_metadata?.theme_color || string_to_color(node.at)
					: "#b7b7b7ff",
				url: new URL(node.at),
				label:
					new URL(node.at).hostname.replace(no_www, "") +
					(new URL(node.at).pathname === "/" ? "" : new URL(node.at).pathname)
			})),
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
