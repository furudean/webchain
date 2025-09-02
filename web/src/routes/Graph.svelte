<script lang="ts">
	import { onMount } from "svelte"
	import type { Sigma, Camera } from "sigma"
	import type GraphType from "graphology"
	import { calculate_tree_layout, build_graph } from "$lib/graph"
	import type { Node } from "$lib/node"
	import type ForceSupervisor from "graphology-layout-force/worker"

	let graph_element: HTMLElement

	let { nodes }: { nodes: Node[] } = $props()

	function update_camera(camera: Camera): void {
		const size = `${100 / camera.ratio}px`
		graph_element.style.backgroundSize = `${size} ${size}`

		const pos_x = `${50 - (camera.x * 100) / camera.ratio}%`
		const pos_y = `${50 + (camera.y * 100) / camera.ratio}%`
		graph_element.style.backgroundPosition = `${pos_x} ${pos_y}`
	}

	function clear_highlighted(graph: GraphType): void {
		for (const node of graph.nodes()) {
			graph.setNodeAttribute(node, "highlighted", false)
		}
	}

	onMount(() => {
		let renderer: Sigma
		let layout: ForceSupervisor

		const init_graph = async () => {
			const { default: Sigma } = await import("sigma")
			const { default: Graph } = await import("graphology")
			const { NodeImageProgram } = await import("@sigma/node-image")
			const { NodeSquareProgram } = await import("@sigma/node-square")
			const { default: ForceSupervisor } = await import(
				"graphology-layout-force/worker"
			)
			const hashmap = new Map(
				Object.values(nodes).map((node, i) => [i.toString(), node])
			)

			const positions = calculate_tree_layout(hashmap)
			const graph = build_graph(hashmap, positions, Graph)
			renderer = new Sigma(graph, graph_element, {
				nodeProgramClasses: {
					image: NodeImageProgram,
					square: NodeSquareProgram
				},
				labelSize: 10,
				labelFont: 'system-ui, sans-serif',
				labelDensity: 0.7,
				labelGridCellSize: 70,
				labelRenderedSizeThreshold: 12,
				maxCameraRatio: 4,
				minCameraRatio: 0.75,
				zoomingRatio: 0.7,
				zoomDuration: 200,
				enableCameraRotation: false,
				cameraPanBoundaries: {
					tolerance: 400
				}
			})

			let dragged_node: string | null = null
			let is_dragging = false

			layout = new ForceSupervisor(graph, {
				isNodeFixed(_, attr) {
					return attr.highlighted
				},
				settings: {}
			})
			if (document.hasFocus()) {
				layout.start()
			}
			window.addEventListener("blur", () => layout?.stop())
			window.addEventListener("focus", () => layout?.start())

			renderer.on("enterNode", (e) => {
				const node_attributes = graph.getNodeAttributes(e.node)
				// show overlay
				graph_element.style.cursor = "pointer"
			})

			renderer.on("leaveNode", () => {
				// hide overlay
				graph_element.style.cursor = ""
			})

			renderer.on("doubleClickNode", (e) => {
				e.preventSigmaDefault()
				const node_attributes = graph.getNodeAttributes(e.node)
				if (node_attributes.url) {
					window.open(node_attributes.url, "_blank")
				}
			})

			renderer.on("downNode", (e) => {
				is_dragging = true
				dragged_node = e.node
				clear_highlighted(graph)
				graph.setNodeAttribute(dragged_node, "highlighted", true)
				if (!renderer.getCustomBBox())
					renderer.setCustomBBox(renderer.getBBox())
				graph_element.style.cursor = "grabbing"
			})

			renderer.on("moveBody", ({ event }) => {
				if (!is_dragging || !dragged_node) return

				const pos = renderer.viewportToGraph(event)

				graph.setNodeAttribute(dragged_node, "x", pos.x)
				graph.setNodeAttribute(dragged_node, "y", pos.y)

				event.preventSigmaDefault()
				event.original.preventDefault()
				event.original.stopPropagation()
			})

			function handle_up() {
				// if (dragged_node) {
				// 	graph.removeNodeAttribute(dragged_node, "highlighted")
				// }
				is_dragging = false
				dragged_node = null
				graph_element.style.cursor = ""
			}
			renderer.on("upNode", handle_up)
			renderer.on("downStage", (event) => {
				clear_highlighted(graph)
			})

			const camera = renderer.getCamera()
			camera.setState({
				ratio: 1.3
			})
			camera.addListener("updated", update_camera)
			update_camera(camera)
		}

		init_graph().catch(console.error)

		return function onDestroy() {
			renderer?.kill()
			layout?.kill()
		}
	})
</script>

<div class="graph-container">
	<div class="graph" bind:this={graph_element}></div>
</div>

<style>
	.graph-container {
		grid-area: graph;
		position: relative;
		overflow: hidden;
	}

	.graph {
		width: 100%;
		height: 100%;
		background-image:
			linear-gradient(to right, hsl(209, 100%, 94%) 1px, transparent 1px),
			linear-gradient(to bottom, hsl(209, 100%, 94%) 1px, transparent 1px);
		/* background-size: 83.3333px 83.3333px;
		background-position: 8.33333% 91.6667%; */
	}

	.graph:active {
		cursor: move;
	}

	/* @media (prefers-color-scheme: dark) {
		#graph {
			background-image:
				linear-gradient(to right, hsl(0, 0%, 15%) 1px, transparent 1px),
				linear-gradient(to bottom, hsl(0, 0%, 15%) 1px, transparent 1px);
			background-color: #181818;
		}
	} */
</style>
