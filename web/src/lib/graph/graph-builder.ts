import type GraphType from "graphology"
import type { Node } from "$lib/node"
import type FA2LayoutSupervisor from "graphology-layout-forceatlas2/worker"

export async function buildGraph(
	hashmap: Map<string, Node>,
	positions: Map<string, { x: number; y: number }>,
	Graph: typeof GraphType
): Promise<{ graph: GraphType; layout_supervisor: FA2LayoutSupervisor }> {
	const { default: forceAtlas2 } = await import("graphology-layout-forceatlas2")
	const { default: FA2LayoutSupervisor } = await import(
		"graphology-layout-forceatlas2/worker"
	)

	const graph = new Graph()

	// Add nodes
	for (const [id, node] of hashmap.entries()) {
		const pos = positions.get(id) || { x: 0, y: 0 }
		const url = new URL(node.at)
		const label = url.hostname + (url.pathname === "/" ? "" : url.pathname)

		// Calculate size based on depth - root is bigger, then gradually shrink
		const base_size = 24
		// const scale = Math.max(0.5, 1 - node.depth * 0.05)

		graph.addNode(id, {
			label: label,
			size: base_size,
			x: pos.x,
			y: pos.y,
			type: node.depth === 0 ? "square" : "image",
			image:
				node.indexed && node.depth !== 0
					? `/api/favicon?url=${encodeURIComponent(node.at)}`
					: undefined,
			url: node.at,
			color: node.color
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
					color: "#efefefff",
					type: "arrow"
				})
			}
		}
	}

	const layout_supervisor = new FA2LayoutSupervisor(graph, {
		settings: {
			...forceAtlas2.inferSettings(graph),
			scalingRatio: 1000,
			gravity: 0.3,
			slowDown: 1000,
		}
	})

	return { graph, layout_supervisor }
}
