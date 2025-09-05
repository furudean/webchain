import type { PageServerLoad } from "./$types"
import type { CrawledNode, Node } from "$lib/node"
import { string_to_color } from "$lib/color"

export const load: PageServerLoad = async ({
	fetch
}): Promise<{
	nodes: Node[]
	start: Date | null
	end: Date | null
}> => {
	const request = await fetch("https://webchain.milkmedicine.net/crawler/data.json")
	// const request = await fetch("/crawler/data.json")

	if (!request.ok) {
		throw new Error("Failed to fetch data")
	}

	try {
		const {
			nodes,
			start,
			end
		}: {
			nodes: CrawledNode[]
			start: string
			end: string
		} = await request.json()

		return {
			nodes: nodes.map((node) => ({
				...node,
				color: string_to_color(node.at),
				url: new URL(node.at)
			})),
			start: new Date(start),
			end: new Date(end)
		}
	} catch (error) {
		console.error("Error parsing JSON:", error)
		return {
			nodes: [],
			start: null,
			end: null
		}
	}
}
