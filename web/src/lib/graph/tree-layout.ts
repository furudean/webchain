import type { Node } from "$lib/node"

export const calculateTreeLayout = (hashmap: Map<string, Node>) => {
	const positions = new Map<string, { x: number; y: number }>()

	// Find root node (node with no parent)
	const rootNode = Array.from(hashmap.entries()).find(
		([, node]) => !node.parent
	)
	if (!rootNode) return positions

	const [rootId] = rootNode

	// Build adjacency map for children
	const childrenMap = new Map<string, string[]>()
	for (const [id, node] of hashmap.entries()) {
		if (node.parent) {
			const parentId = Array.from(hashmap.entries()).find(
				([, n]) => n.at === node.parent
			)?.[0]
			if (parentId) {
				if (!childrenMap.has(parentId)) {
					childrenMap.set(parentId, [])
				}
				childrenMap.get(parentId)!.push(id)
			}
		}
	}

	// Calculate subtree width (number of leaf nodes)
	function getSubtreeWidth(nodeId: string): number {
		const children = childrenMap.get(nodeId) || []
		if (children.length === 0) return 1 // leaf node

		return children.reduce(
			(total, childId) => total + getSubtreeWidth(childId),
			0
		)
	}

	// Position nodes using radial tree layout with multiple growth directions
	function positionSubtree(
		nodeId: string,
		centerX: number,
		centerY: number,
		radius: number,
		startAngle: number,
		angleSpan: number,
		depth: number = 0
	) {
		positions.set(nodeId, { x: centerX, y: centerY })

		const children = childrenMap.get(nodeId) || []
		if (children.length === 0) return

		// Calculate next level parameters with inverse depth-based spacing
		const depthMultiplier = Math.max(0, 1 - depth)
		const nextRadius = radius + depthMultiplier
		const anglePerChild = angleSpan / children.length

		children.forEach((childId, index) => {
			// Calculate angle for this child
			const childAngle = startAngle + (index + 0.5) * anglePerChild

			// Calculate position using polar coordinates
			const childX = centerX + Math.cos(childAngle) * nextRadius
			const childY = centerY + Math.sin(childAngle) * nextRadius

			// Calculate angle span for this child's subtree
			const childSubtreeWidth = getSubtreeWidth(childId)
			const totalSubtreeWidth = children.reduce(
				(sum, id) => sum + getSubtreeWidth(id),
				0
			)
			const childAngleSpan = (childSubtreeWidth / totalSubtreeWidth) * angleSpan

			// Recursively position child's subtree
			positionSubtree(
				childId,
				childX,
				childY,
				nextRadius,
				childAngle - childAngleSpan / 2,
				childAngleSpan,
				depth + 1
			)
		})
	}

	// Start positioning from root with radial layout covering full circle
	positionSubtree(rootId, 0, 0, 0, 0, Math.PI * 2, 0) // Start at center, full 360° coverage

	return positions
}
