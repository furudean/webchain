import type { PageServerLoad } from "./$types"
import type { Node } from "$lib/node"

export const load: PageServerLoad = async (): Promise<{
	nodes: Node[]
	timestamp: string | null
}> => {
	const request = await fetch(
		"https://webchain.milkmedicine.net/crawler/data.json"
	)

	if (!request.ok) {
		throw new Error("Failed to fetch data")
	}

	try {
		const { nodes, timestamp } = await request.json()

		return {
			nodes,
			timestamp
		}
	} catch (error) {
		console.error("Error parsing JSON:", error)
		return {
			nodes: [],
			timestamp: null
		}
	}
}
