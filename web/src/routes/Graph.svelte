<script lang="ts">
	import { onDestroy, onMount } from "svelte"
	import type { Sigma, Camera } from "sigma"
	import type GraphType from "graphology"
	import { calculate_tree_layout, build_graph } from "$lib/graph"
	import type { Node } from "$lib/node"
	import {
		hovered_node,
		graph as graph_store,
		set_highlighted_node
	} from "$lib/node_state"
	import { page } from "$app/state"
	import type { default as ForceSupervisorType } from "graphology-layout-force/worker"

	let { nodes }: { nodes: Node[] } = $props()

	const highlighted_node = $derived(page.state.node)
	let graph_element: HTMLElement
	const display_node = $derived($hovered_node || highlighted_node)

	let graph: GraphType | undefined = $state()
	let renderer: Sigma | undefined = $state()
	let layout: ForceSupervisorType | undefined = $state()
	let last_x: number | undefined = $state()
	let last_y: number | undefined = $state()

	function update_camera(camera: Camera): void {
		const size = `${100 / camera.ratio}px`
		graph_element.style.backgroundSize = `${size} ${size}`

		const pos_x = `${50 - (camera.x * 100) / camera.ratio}%`
		const pos_y = `${50 + (camera.y * 100) / camera.ratio}%`
		graph_element.style.backgroundPosition = `${pos_x} ${pos_y}`
	}

	async function init_graph(): Promise<void> {
		const { default: Sigma } = await import("sigma")
		const { default: Graph } = await import("graphology")
		const { NodeImageProgram } = await import("@sigma/node-image")
		const { NodeSquareProgram } = await import("@sigma/node-square")
		const { default: ForceSupervisor } = await import(
			"graphology-layout-force/worker"
		)
		const hashmap = new Map(Object.values(nodes).map((node) => [node.at, node]))

		const positions = calculate_tree_layout(hashmap)
		graph = build_graph(hashmap, positions, Graph)
		graph_store.set(graph)
		renderer = new Sigma(graph, graph_element, {
			nodeProgramClasses: {
				image: NodeImageProgram,
				square: NodeSquareProgram
			},
			labelSize: 10,
			labelFont: "system-ui, sans-serif",
			labelDensity: 0.7,
			labelGridCellSize: 70,
			labelRenderedSizeThreshold: 12,
			maxCameraRatio: 4,
			minCameraRatio: 0.75,
			zoomingRatio: 0.7,
			zoomDuration: 200,
			enableCameraRotation: false,
			cameraPanBoundaries: {
				tolerance: 250
			},
			stagePadding: 125,
			autoRescale: true,
			autoCenter: true,
		})

		let dragged_node: string | null = null
		let is_dragging = false

		layout = new ForceSupervisor(graph, {
			isNodeFixed(_, attr) {
				return attr.highlighted
			},
			settings: {
				// repulsion: 0.2
			}
		})
		if (!document.hidden) {
			layout.start()
		}
		window.addEventListener("visibilitychange", (e) => {
			if (document.hidden) {
				layout?.stop()
			} else {
				layout?.start()
			}
		})
		window.addEventListener("focus", () => layout?.start())

		renderer.on("enterNode", (e) => {
			graph_element.style.cursor = "pointer"
			hovered_node.set(e.node)
		})

		renderer.on("leaveNode", (e) => {
			graph_element.style.cursor = ""
			hovered_node.set(undefined)
		})

		renderer.on("doubleClickNode", (e) => {
			if (!graph) return
			e.preventSigmaDefault()
			const node_attributes = graph.getNodeAttributes(e.node)
			if (node_attributes.url) {
				window.open(node_attributes.url, "_blank")
			}
		})

		renderer.on("downNode", (e) => {
			if (!graph || !renderer) return
			is_dragging = true
			dragged_node = e.node
			hovered_node.set(e.node)
			set_highlighted_node(e.node)
			if (!renderer.getCustomBBox()) renderer.setCustomBBox(renderer.getBBox())
			graph_element.style.cursor = "grabbing"
		})

		renderer.on("moveBody", ({ event }) => {
			if (!graph || !renderer) return
			if (!is_dragging || !dragged_node) return

			const pos = renderer.viewportToGraph(event)

			graph.setNodeAttribute(dragged_node, "x", pos.x)
			graph.setNodeAttribute(dragged_node, "y", pos.y)

			last_x = pos.x
			last_y = pos.y

			event.preventSigmaDefault()
			event.original.preventDefault()
			event.original.stopPropagation()
		})

		renderer.on("doubleClickStage", (e) => {
			e.preventSigmaDefault()
		})

		renderer.on("upNode", () => {
			is_dragging = false
			dragged_node = null
			graph_element.style.cursor = "grab"
		})
		renderer.on("leaveStage", ({ event }) => {
			graph_element.style.cursor = ""
		})
		renderer.on("upStage", () => {
			set_highlighted_node(undefined)
		})

		const camera = renderer.getCamera()
		camera.addListener("updated", update_camera)
		update_camera(camera)
	}

	onMount(() => {
		init_graph().catch(console.error)

		return () => {
			layout?.kill()
			renderer?.kill()
		}
	})

	$effect(() => {
		if (!graph) return

		for (const node of graph.nodes()) {
			graph.setNodeAttribute(node, "highlighted", false)
		}
		if (highlighted_node) {
			graph.setNodeAttribute(highlighted_node, "highlighted", true)
		}
	})
</script>

<div class="graph-container">
	{#if display_node}
		{#key last_x || last_y}
			<pre aria-hidden="true">{JSON.stringify(
					graph?.getNodeAttributes(display_node),
					null,
					2
				)}</pre>
		{/key}
	{/if}
	<div class="graph" bind:this={graph_element}></div>
</div>

<style>
	.graph-container {
		grid-area: graph;
		overflow: hidden;
		position: relative;
		display: flex;
	}

	pre {
		position: fixed;
		top: -0.5em;
		left: 0;
		font-family: monospace;
		font-size: 7vh;
		opacity: 0.02;
		margin: 0;
	}

	.graph {
		position: fixed;
		top: 0;
		left: 0;
		width: 100vw;
		height: 100vh;
		background-image:
			linear-gradient(to right, hsl(209, 100%, 97%) 1px, transparent 1px),
			linear-gradient(to bottom, hsl(209, 100%, 90%) 1px, transparent 1px);
		background-repeat: none;
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
