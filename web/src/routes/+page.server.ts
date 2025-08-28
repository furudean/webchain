import type { PageServerLoad } from "./$types"
import type { Node } from "$lib/node"

export const load: PageServerLoad = async () => {
	const request = await fetch(
		"https://webchain.milkmedicine.net/crawler/data.json"
	)

	if (!request.ok) {
		throw new Error("Failed to fetch data")
	}

	const nodes = (await request.json()) as Node[]

	return {
		nodes
	}
}
