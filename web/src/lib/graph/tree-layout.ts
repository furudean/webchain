import type { DisplayNode } from "$lib/node"

export function calculate_tree_layout(hashmap: Map<string, DisplayNode>) {
	const positions = new Map<string, { x: number; y: number }>()

	// Find root node (node with no parent)
	const rootNode = Array.from(hashmap.entries()).find(
		([, node]) => !node.parent
	)
	if (!rootNode) return positions

	const [rootId] = rootNode

	// Build adjacency map for children
	const child_map = new Map<string, string[]>()
	for (const [id, node] of hashmap.entries()) {
		if (node.parent) {
			const parent_id = Array.from(hashmap.entries()).find(
				([, n]) => n.at === node.parent
			)?.[0]
			if (parent_id) {
				if (!child_map.has(parent_id)) {
					child_map.set(parent_id, [])
				}
				child_map.get(parent_id)!.push(id)
			}
		}
	}

	// Simplified radial layout
	function position_subtree(
		nodeId: string,
		centerX: number,
		centerY: number,
		radius: number,
		angle: number,
		angleStep: number
	) {
		positions.set(nodeId, { x: centerX, y: centerY })

		const children = child_map.get(nodeId) || []
		if (children.length === 0) return

		const nextRadius = radius + 1 // Increment radius for the next level
		children.forEach((childId, index) => {
			const childAngle = angle + index * angleStep
			const childX = centerX + Math.cos(childAngle) * nextRadius
			const childY = centerY + Math.sin(childAngle) * nextRadius

			position_subtree(
				childId,
				childX,
				childY,
				nextRadius,
				childAngle,
				angleStep
			)
		})
	}

	// Start positioning from root with a full circle layout
	const totalChildren = child_map.get(rootId)?.length || 1
	const angleStep = (2 * Math.PI) / totalChildren
	position_subtree(rootId, 0, 0, 0, 0, angleStep)

	return positions
}
