import type GraphType from "graphology"
import type { Node } from "$lib/node"

export async function buildGraph(
	hashmap: Map<string, Node>,
	positions: Map<string, { x: number; y: number }>,
	Graph: typeof GraphType
): Promise<GraphType> {
	const graph = new Graph()

	// Add nodes
	for (const [id, node] of hashmap.entries()) {
		const pos = positions.get(id) || { x: 0, y: 0 }
		const url = new URL(node.at)
		const label = url.hostname + (url.pathname === "/" ? "" : url.pathname)

		// Calculate size based on depth - root is bigger, then gradually shrink
		const base_size = 20
		const scale = Math.max(0.5, 1 - node.depth * 0.06)

		graph.addNode(id, {
			label: label,
			size: base_size * scale,
			x: pos.x,
			y: pos.y,
			type: node.depth === 0 ? "square" : "image",
			image:
				node.indexed && node.depth !== 0
					? `/api/favicon?url=${encodeURIComponent(node.at)}`
					: undefined,
			url: node.at,
			color: node.color,
		})
	}

	// Add edges
	for (const [id, node] of hashmap.entries()) {
		if (node.parent) {
			const parent_id = Array.from(hashmap.entries()).find(
				([, n]) => n.at === node.parent
			)?.[0]
			if (parent_id) {
				graph.addEdge(parent_id, id, {
					size: 3,
					color: "#e0e0e0ff",
					type: "arrow"
				})
			}
		}
	}



	return graph
}
