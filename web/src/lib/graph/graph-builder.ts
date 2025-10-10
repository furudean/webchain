import type GraphType from "graphology"
import type { DisplayNode } from "$lib/node"

export function build_graph(
	hashmap: Map<string, DisplayNode>,
	// positions: Map<string, { x: number; y: number }>,
	Graph: typeof GraphType
): GraphType {
	const graph = new Graph()

	// Add nodes
	for (const [id, node] of hashmap.entries()) {
		graph.addNode(id, {
			label: node.label,
			size: 20,
			x: Math.random(),
			y: Math.random(),
			type: node.depth === 0 ? "square" : "image",
			image: `/api/favicon?url=${encodeURIComponent(node.at)}`,
			url: node.at,
			color: node.generated_color
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
					color: "#dedede",
					type: "arrow"
				})
			}
		}
	}

	return graph
}
