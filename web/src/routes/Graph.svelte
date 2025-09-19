<script lang="ts">
	import { onMount } from "svelte"
	import type { Sigma, Camera } from "sigma"
	import type { AnimateOptions } from "sigma/utils"
	import type GraphType from "graphology"
	import { calculate_tree_layout, build_graph } from "$lib/graph"
	import type { Node } from "$lib/node"
	import {
		hovered_node,
		graph as graph_store,
		set_highlighted_node
	} from "$lib/node-state"
	import { page } from "$app/state"
	import type { default as ForceSupervisorType } from "graphology-layout-force/worker"
	import { getCameraStateToFitViewportToNodes } from "@sigma/utils"

	let { nodes }: { nodes: Node[] } = $props()

	const highlighted_node = $derived(page.state.node)
	const display_node = $derived($hovered_node || highlighted_node)

	let graph: GraphType | undefined = $state()
	let renderer: Sigma | undefined = $state()
	let layout: ForceSupervisorType | undefined = $state()
	let last_x: number | undefined = $state()
	let last_y: number | undefined = $state()

	let zoom_frame: number | null = null
	let graph_element: HTMLElement

	function update_camera(camera: Camera): void {
		const size = `${100 / camera.ratio}px`
		graph_element.style.backgroundSize = `${size} ${size}`

		const pos_x = `${50 - (camera.x * 100) / camera.ratio}%`
		const pos_y = `${50 + (camera.y * 100) / camera.ratio}%`
		graph_element.style.backgroundPosition = `${pos_x} ${pos_y}`
	}

	export async function center_on_nodes(
		nodes: string[] | undefined = undefined,
		options: Partial<AnimateOptions> = {}
	): Promise<void> {
		if (!renderer) return
		nodes = typeof nodes === "undefined" ? (graph?.nodes() ?? []) : nodes
		const camera_state = getCameraStateToFitViewportToNodes(renderer, nodes)
		camera_state.ratio *= 1.1 // add some padding
		await renderer.getCamera()?.animate(camera_state, options)
	}

	function zoom(direction: 1 | -1): void {
		const camera = renderer?.getCamera()
		if (!camera) return
		const factor = 1.025
		camera.setState({
			ratio: camera.ratio * (direction < 1 ? factor : 1 / factor)
		})
	}

	function zoom_loop(direction: 1 | -1): void {
		zoom(direction)
		zoom_frame = requestAnimationFrame(() => zoom_loop(direction))
	}

	function start_zoom(direction: 1 | -1): void {
		if (zoom_frame === null) {
			zoom(direction)
			zoom_frame = requestAnimationFrame(() => zoom_loop(direction))
		}
	}
	function stop_zoom(): void {
		if (zoom_frame !== null) {
			cancelAnimationFrame(zoom_frame)
			zoom_frame = null
		}
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
			maxCameraRatio: 8,
			minCameraRatio: 0.75,
			stagePadding: 125
		})

		let dragged_node: string | null = null
		let is_dragging = false

		layout = new ForceSupervisor(graph, {
			isNodeFixed(_, attr) {
				return attr.highlighted
			},
			settings: {
				inertia: 0.6
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
			graph_element.style.cursor = "grab"
			hovered_node.set(e.node)
		})

		renderer.on("leaveNode", async (e) => {
			hovered_node.set(undefined)
			graph_element.style.cursor = ""
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
			set_highlighted_node(e.node, hashmap.get(e.node)?.url_param)
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

		renderer.on("upNode", () => {
			is_dragging = false
			dragged_node = null
			graph_element.style.cursor = "grab"
		})
		renderer.on("leaveStage", ({ event }) => {
			graph_element.style.cursor = ""
		})
		renderer.on("upStage", (e) => {
			if (is_dragging) {
				e.preventSigmaDefault()
				set_highlighted_node(undefined)
			}
		})
		renderer.on("clickStage", () => {
			if (highlighted_node) {
				set_highlighted_node(undefined)
			} else {
				center_on_nodes()
			}
		})
		renderer.on("doubleClickStage", (e) => {
			e.preventSigmaDefault()
		})

		const camera = renderer.getCamera()
		camera.addListener("updated", update_camera)
		update_camera(camera)
		camera.setState({
			ratio: 3
		})
		setTimeout(() => {
			center_on_nodes(undefined, {
				duration: 650,
				easing: "cubicInOut"
			})
		}, 400)
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
			graph.setNodeAttribute(node, "highlighted", node === highlighted_node)
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

	<div class="camera-controls">
		<button
			onclick={() => {
				center_on_nodes()
			}}
			title="Reset camera view"
			aria-label="Reset camera view"
		>
			<svg
				width="20"
				height="20"
				viewBox="0 0 20 20"
				aria-hidden="true"
				focusable="false"
			>
				<path d="M6 8V6H8" stroke="currentColor" stroke-width="1" fill="none" />
				<path
					d="M14 8V6H12"
					stroke="currentColor"
					stroke-width="1"
					fill="none"
				/>
				<path
					d="M14 12V14H12"
					stroke="currentColor"
					stroke-width="1"
					fill="none"
				/>
				<path
					d="M6 12V14H8"
					stroke="currentColor"
					stroke-width="1"
					fill="none"
				/>
			</svg>
		</button>
		<button
			onpointerdown={() => start_zoom(1)}
			onpointerup={stop_zoom}
			onpointerleave={stop_zoom}
			title="Zoom in">+</button
		>
		<button
			onpointerdown={() => start_zoom(-1)}
			onpointerup={stop_zoom}
			onpointerleave={stop_zoom}
			title="Zoom out">-</button
		>
	</div>
</div>

<style>
	.graph-container {
		grid-area: graph;
		overflow: hidden;
		position: relative;
		display: flex;
	}

	.camera-controls {
		position: fixed;
		right: 1em;
		bottom: 1.9em;
		z-index: 10;
		display: flex;
		flex-direction: column;
		gap: 0.5em;
	}
	.camera-controls button {
		all: unset;
		width: 1.5em;
		height: 1.5em;
		font-size: 1em;
		background-color: #ffffffd8;
		border: 1px solid #ccc;
		color: #333;
		display: flex;
		align-items: center;
		justify-content: center;
		user-select: none;
		backdrop-filter: blur(2px);
	}

	.camera-controls button:active {
		background-color: #eee;
	}

	pre {
		position: fixed;
		top: -0.5em;
		left: 0;
		font-family: monospace;
		font-size: 9.25vh;
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
