import type GraphType from "graphology"
import type { Node } from "$lib/node"
import { string_to_color } from "$lib/color"

export function buildGraph(
	hashmap: Map<string, Node>,
	positions: Map<string, { x: number; y: number }>,
	Graph: typeof GraphType
): GraphType {
	const graph = new Graph()

	// Add nodes
	for (const [id, node] of hashmap.entries()) {
		const pos = positions.get(id) || { x: 0, y: 0 }
		const url = new URL(node.at)
		const label = url.hostname + (url.pathname === "/" ? "" : url.pathname)

		// Calculate size based on depth - root is bigger, then gradually shrink
		const baseSize = 24
		const sizeReduction = Math.max(0.5, 1 - node.depth * 0.05)
		const nodeSize = baseSize * sizeReduction

		graph.addNode(id, {
			label: label,
			size: nodeSize,
			x: pos.x,
			y: pos.y,
			type: node.depth === 0 ? 'square' : 'image',
			image: node.indexed && node.depth !== 0
				? `/api/favicon?url=${encodeURIComponent(node.at)}`
				: undefined,
			url: node.at,
			color: string_to_color(node.at)
		})
	}

	// Add edges
	for (const [id, node] of hashmap.entries()) {
		if (node.parent) {
			const parentId = Array.from(hashmap.entries()).find(
				([, n]) => n.at === node.parent
			)?.[0]
			if (parentId) {
				graph.addEdge(parentId, id, {
					size: 3,
					color: "#e5e5e5",
					type: "arrow",
				})
			}
		}
	}

	return graph
}
