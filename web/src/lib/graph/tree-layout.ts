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

	function get_leaf_nodes(nodeId: string): number {
		const children = child_map.get(nodeId) || []
		if (children.length === 0) return 1 // leaf node

		return children.reduce(
			(total, childId) => total + get_leaf_nodes(childId),
			0
		)
	}

	// Position nodes using radial tree layout with multiple growth directions
	function position_subtree(
		nodeId: string,
		centerX: number,
		centerY: number,
		radius: number,
		startAngle: number,
		angleSpan: number,
		depth: number = 0
	) {
		positions.set(nodeId, { x: centerX, y: centerY })

		const children = child_map.get(nodeId) || []
		if (children.length === 0) return

		//  next level parameters with inverse depth-based spacing
		const depthMultiplier = Math.max(0, 1 - depth)
		const nextRadius = radius + depthMultiplier
		const anglePerChild = angleSpan / children.length

		children.forEach((childId, index) => {
			// angle for this child
			const childAngle = startAngle + (index + 0.5) * anglePerChild

			// position using polar coordinates
			const childX = centerX + Math.cos(childAngle) * nextRadius
			const childY = centerY + Math.sin(childAngle) * nextRadius

			// angle span for this child's subtree
			const child_subtree_width = get_leaf_nodes(childId)
			const total_subtree_width = children.reduce(
				(sum, id) => sum + get_leaf_nodes(id),
				0
			)
			const childAngleSpan =
				(child_subtree_width / total_subtree_width) * angleSpan

			position_subtree(
				childId,
				childX,
				childY,
				nextRadius,
				childAngle - childAngleSpan,
				childAngleSpan,
				depth + 1
			)
		})
	}

	// start positioning from root with radial layout covering full circle
	position_subtree(rootId, 0, 0, 0, 0, Math.PI * 2, 0)

	return positions
}
