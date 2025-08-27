import Graph from "graphology"
import type { Node } from "./tree-layout.js"

export function buildGraph(
	hashmap: Map<string, Node>,
	positions: Map<string, { x: number; y: number }>
): Graph {
	const graph = new Graph()

	// Add nodes
	for (const [id, node] of hashmap.entries()) {
		const pos = positions.get(id) || { x: 0, y: 0 }
		const url = new URL(node.at)
		const label = url.hostname + (url.pathname === "/" ? "" : url.pathname)


		// Calculate size based on depth - root is bigger, then gradually shrink
		const baseSize = 25
		const sizeReduction = Math.max(0.5, 1 - (node.depth * 0.05))
		const nodeSize = baseSize * sizeReduction

		graph.addNode(id, {
			label: label,
			size: nodeSize,
			x: pos.x,
			y: pos.y,
			type: "image",
			image: node.indexed ? `/api/favicon?url=${encodeURIComponent(node.at)}` : undefined,
			url: node.at,
		})
	}

	// Add edges
	for (const [id, node] of hashmap.entries()) {
		if (node.parent) {
			const parentId = Array.from(hashmap.entries()).find(
				([, n]) => n.at === node.parent
			)?.[0]
			if (parentId) {
				graph.addEdge(parentId, id)
			}
		}
	}

	return graph
}
