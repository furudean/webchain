import type GraphType from "graphology"
import type { Node } from "$lib/node"

export function build_graph(
	hashmap: Map<string, Node>,
	positions: Map<string, { x: number; y: number }>,
	Graph: typeof GraphType
): GraphType {
	const graph = new Graph()

	// Add nodes
	for (const [id, node] of hashmap.entries()) {
		const pos = positions.get(id) || { x: 0, y: 0 }

		// Calculate size based on depth - root is bigger, then gradually shrink
		const base_size = 20
		const scale = Math.max(0.5, 1 - node.depth * 0.06)

		graph.addNode(id, {
			label: node.label,
			size: base_size * scale,
			labelWeight: node.depth === 0 ? "bold" : "normal",

			x: pos.x,
			y: pos.y,
			type: node.depth === 0 ? "square" : "image",
			image:
				node.indexed && node.depth !== 0
					? `/api/favicon?url=${encodeURIComponent(node.at)}`
					: undefined,
			url: node.at,
			color: node.color,
			indexed: node.indexed
		})
	}

	// Add edges
	for (const [id, node] of hashmap.entries()) {
		if (node.parent) {
			const parent_id = Array.from(hashmap.values()).find(
				(n) => n.at === node.parent
			)?.at
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
