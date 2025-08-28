import type { PageServerLoad } from "./$types"
import type { Node } from "$lib/node"

export const load: PageServerLoad = async (): Promise<{
	nodes: Node[]
	start: string | null
	end: string | null
}> => {
	const request = await fetch(
		"https://webchain.milkmedicine.net/crawler/data.json"
	)

	if (!request.ok) {
		throw new Error("Failed to fetch data")
	}

	try {
		const { nodes, start, end } = await request.json()

		return {
			nodes,
			start,
			end,
		}
	} catch (error) {
		console.error("Error parsing JSON:", error)
		return {
			nodes: [],
			start: null,
			end: null,
		}
	}
}
