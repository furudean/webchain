<script lang="ts">
	import { onMount } from "svelte"
	import type { Sigma, Camera } from "sigma"
	import { calculateTreeLayout, buildGraph } from "$lib/graph"
	import type { Node } from "$lib/node"
	import type ForceSupervisor from "graphology-layout-force/worker"

	let graph_element: HTMLElement

	let { nodes }: { nodes: Node[] } = $props()

	function update_camera(camera: Camera) {
		const size = `${100 / camera.ratio}px`
		graph_element.style.backgroundSize = `${size} ${size}`

		const pos_y = `${50 - (camera.x * 100) / camera.ratio}%`
		const pos_x = `${50 + (camera.y * 100) / camera.ratio}%`
		graph_element.style.backgroundPosition = `${pos_y} ${pos_x}`
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

			const positions = calculateTreeLayout(hashmap)
			const graph = await buildGraph(hashmap, positions, Graph)
			renderer = new Sigma(graph, graph_element, {
				nodeProgramClasses: {
					image: NodeImageProgram,
					square: NodeSquareProgram
				},
				labelSize: 10,
				labelDensity: 0.7,
				labelGridCellSize: 70,
				labelRenderedSizeThreshold: 13,
				maxCameraRatio: 4,
				minCameraRatio: 0.75,
				enableCameraRotation: false,
				cameraPanBoundaries: {
					tolerance: 400
				},
			})

			let dragged_node: string | null = null
			let is_dragging = false

			layout = new ForceSupervisor(graph, {
				isNodeFixed(_, attr) {
					return attr.highlighted
				},
				settings: {},
			})
			if (document.hasFocus()) {
				layout.start()
			}

			renderer.on("downNode", (e) => {
				is_dragging = true
				dragged_node = e.node
				graph.setNodeAttribute(dragged_node, "highlighted", true)
				if (!renderer.getCustomBBox())
					renderer.setCustomBBox(renderer.getBBox())
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
				if (dragged_node) {
					graph.removeNodeAttribute(dragged_node, "highlighted")
				}
				is_dragging = false
				dragged_node = null
			}
			renderer.on("upNode", handle_up)
			renderer.on("upStage", handle_up)

			const camera = renderer.getCamera()
			camera.setState({
				ratio: 1.2
			})
			camera.addListener("updated", update_camera)
			update_camera(camera)
			window.addEventListener("blur", () => layout?.stop())
			window.addEventListener("focus", () => layout?.start())
		}

		init_graph().catch(console.error)

		return function onDestroy() {
			renderer?.kill()
			layout?.kill()
		}
	})
</script>

<div id="graph" bind:this={graph_element}></div>

<style>
	#graph {
		grid-area: graph;
		width: 100%;
		height: 100vh;

		background-image:
			linear-gradient(to right, hsl(0, 0%, 95%) 1px, transparent 1px),
			linear-gradient(to bottom, hsl(0, 0%, 95%) 1px, transparent 1px);
		background-size: 83.3333px 83.3333px;
		background-position: 8.33333% 91.6667%;
		cursor: grab;
	}

	#graph:active {
		cursor: grabbing;
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
