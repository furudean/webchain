<script lang="ts">
	import { onMount } from "svelte"
	import type { Sigma as SigmaType, Camera } from "sigma"
	import type { AnimateOptions } from "sigma/utils"
	import type GraphType from "graphology"
	import { build_graph } from "$lib/graph"
	import type { DisplayNode } from "$lib/node"
	import { hovered_node, set_highlighted_node } from "$lib/node-state"
	import { page } from "$app/state"
	import type { default as ForceSupervisorType } from "graphology-layout-force/worker"
	import { getCameraStateToFitViewportToNodes } from "@sigma/utils"
	import { browser } from "$app/environment"
	import Spinner from "$lib/Spinner.svelte"

	let { nodes }: { nodes: DisplayNode[] } = $props()

	const highlighted_node = $derived(page.state.node)
	const display_node = $derived($hovered_node || highlighted_node)
	const display_node_data = $derived.by(() =>
		display_node ? nodes.find((n) => n.at === display_node) : undefined
	)

	let graph: GraphType | undefined = $state()
	let renderer: SigmaType | undefined = $state()
	let layout: ForceSupervisorType | undefined = $state()
	let graph_promise: Promise<void> | undefined = $state()

	let zoom_frame: number | null = null
	let graph_element: HTMLElement
	let graph_container: HTMLElement

	function update_camera(camera: Camera): void {
		requestAnimationFrame(() => {
			const size = `${40 / camera.ratio}px`
			graph_container.style.backgroundSize = `${size} ${size}`
			const transparency = Math.max(0.05, 0.5 / camera.ratio)
			const part = "var(--octal-color)"
			graph_container.style.backgroundImage = `radial-gradient(rgb(${part}, ${part}, ${part}, ${transparency}) 1px, transparent 0)`

			let pos_x = "0"
			let pos_y = "0"
			if (renderer && graph) {
				const center = { x: camera.x, y: camera.y }
				const viewport = renderer.graphToViewport(center)
				if (viewport) {
					pos_x = `${viewport.x}px`
					pos_y = `${viewport.y}px`
				}
			}
			graph_container.style.backgroundPosition = `${pos_x} ${pos_y}`
		})
	}

	export async function center_on_nodes(
		nodes: string[] | undefined = undefined,
		options: Partial<AnimateOptions> = {}
	): Promise<void> {
		if (!renderer) return
		nodes = typeof nodes === "undefined" ? (graph?.nodes() ?? []) : nodes
		const camera_state = getCameraStateToFitViewportToNodes(renderer, nodes)
		camera_state.ratio *= 1.5 // add some padding
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

	function is_webgl_supported(): boolean {
		// return false
		if (!browser) return false
		try {
			const canvas = document.createElement("canvas")
			return !!(
				canvas.getContext("webgl") || canvas.getContext("experimental-webgl")
			)
		} catch {
			return false
		}
	}

	function css_var(name: string): string {
		if (!browser) throw new Error("css_var can only be used in the browser")
		const value = getComputedStyle(document.documentElement).getPropertyValue(
			name
		)
		return value.trim()
	}

	async function init_graph(): Promise<void> {
		if (!is_webgl_supported()) throw new Error("webgl not supported")

		const { default: Sigma } = await import("sigma")
		const { default: Graph } = await import("graphology")
		const { NodeImageProgram } = await import("@sigma/node-image")
		const { NodeSquareProgram } = await import("@sigma/node-square")
		const { default: ForceSupervisor } = await import(
			"graphology-layout-force/worker"
		)
		const hashmap = new Map(Object.values(nodes).map((node) => [node.at, node]))

		graph = build_graph(hashmap, Graph)

		renderer = new Sigma(graph, graph_element, {
			nodeProgramClasses: {
				image: NodeImageProgram,
				square: NodeSquareProgram
			},

			labelSize: 10,
			labelFont: '"Fantasque Sans Mono", sans-serif',
			labelColor: { attribute: "textColor" },
			labelGridCellSize: 125,
			labelRenderedSizeThreshold: 10,

			maxCameraRatio: 8,
			minCameraRatio: 0.75,

			nodeReducer(node, data) {
				const res: typeof data = { ...data }
				const faded_color = css_var("--color-graph-inactive")

				res.textColor = css_var("--color-text")

				if (highlighted_node || $hovered_node) {
					const is_highlighted =
						node === highlighted_node || node === $hovered_node
					const is_neighbor = graph!
						.neighbors(highlighted_node || $hovered_node)
						.includes(node)

					if (!is_highlighted && !is_neighbor) {
						// Grey out other nodes
						res.color = faded_color
						res.image = undefined
						res.textColor = css_var("--color-shy")
					}

					if (is_highlighted) {
						// res.textColor = css_var("--color-bg")
						res.textColor = "#222"
					}
				}

				return res
			},
			edgeReducer(edge, data) {
				const res = { ...data }
				const faded_color = css_var("--color-graph-inactive")

				res.color = css_var("--color-graph-edge")

				if (highlighted_node || $hovered_node) {
					const source = graph?.source(edge)
					const target = graph?.target(edge)
					const via_highlight =
						source === highlighted_node || target === highlighted_node
					const via_hover = source === $hovered_node || target === $hovered_node

					if (via_highlight || via_hover) {
						// set edge color to the color of the connected node
						res.color = nodes.find(
							(n) => n.at === (source || target)
						)?.generated_color
					} else {
						res.color = faded_color // Grey out other edges
					}
				}
				return res
			}
		})

		let dragged_node: string | null = null
		let is_dragging = false

		layout = new ForceSupervisor(graph, {
			isNodeFixed(node, attr) {
				return dragged_node === node
			},
			settings: {
				// attraction: 0.0005,
				// repulsion: 0.1,
				// gravity: 0.0001,
				// inertia: 0.6,
				// maxMove: 200
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
			ratio: renderer.getSetting("maxCameraRatio") ?? 0.75
		})
		setTimeout(() => {
			center_on_nodes(undefined, {
				duration: 650,
				easing: "cubicInOut"
			})
		}, 400)
	}

	onMount(() => {
		graph_promise = init_graph()
		graph_promise.catch(console.error)

		window
			.matchMedia("(prefers-color-scheme: dark)")
			.addEventListener("change", (event) => {
				// make sure the graph colors are updated when the color scheme changes
				renderer?.refresh()
			})

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

		// Refresh the renderer and update the tooltip when display_node changes
		renderer?.refresh()

		if (display_node) {
			const loop = () => {
				update_tooltip()
				tooltip_animation_frame = requestAnimationFrame(loop)
			}
			loop()
		} else if (tooltip_animation_frame !== null) {
			cancelAnimationFrame(tooltip_animation_frame)
			tooltip_animation_frame = null
		}
	})

	let tooltip_animation_frame: number | null = null
	let tooltip_style = $state({
		top: "0px",
		left: "0px",
		transform: "translate(-50%, -50%)"
	})

	function update_tooltip() {
		if (!graph || !display_node || !renderer) return

		const attributes = graph.getNodeAttributes(display_node)
		const { x, y } = renderer.graphToViewport({
			x: attributes.x,
			y: attributes.y
		}) || { x: 0, y: 0 }

		const camera = renderer.getCamera()
		const scale = 1 / camera.ratio // Scale tooltip size inversely with zoom ratio

		requestAnimationFrame(() => {
			tooltip_style = {
				top: `${y}px`,
				left: `${x}px`,
				transform: `translate(-50%, -50%) scale(${scale})`
			}
		})
	}
</script>

<div class="graph-container" bind:this={graph_container}>
	{#if display_node}
		<div
			class="tooltip"
			style:top={tooltip_style.top}
			style:left={tooltip_style.left}
			style:transform={tooltip_style.transform}
		>
			<pre>
				<code>{JSON.stringify(display_node_data, null, 2)}</code>
			</pre>
		</div>
	{/if}

	<div id="graph" bind:this={graph_element} class:has-renderer={renderer}></div>

	{#if browser}
		<!-- has javascript, in browser -->
		{#await graph_promise}
			<div class="env-warning">
				<Spinner></Spinner> loading graph...
			</div>
		{:catch error}
			{#if !is_webgl_supported()}
				<div class="env-warning">graph requires webgl to be enabled</div>
			{:else}
				<div class="env-warning">failed to load graph: {error.message}</div>
			{/if}
		{/await}
	{/if}
	<noscript>
		<div class="env-warning">graph requires javascript to be enabled</div>
	</noscript>

	{#if browser}
		{#await graph_promise then}
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
						<path
							d="M6 8V6H8"
							stroke="currentColor"
							stroke-width="1"
							fill="none"
						/>
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
		{/await}
	{/if}
</div>

<style>
	.graph-container {
		overflow: hidden;
		position: fixed;
		inset: 0;
		display: flex;
		background: var(--color-bg);
		background-repeat: none;
		will-change: background-size, background-position, background-image;
	}

	.tooltip {
		position: fixed;
		font-family: "Fantasque Sans Mono", monospace;
		font-size: 0.7rem;
		pointer-events: none;
		color: var(--color-graph-tooltip);
		text-shadow:
			0 0 2px var(--color-bg),
			0 0 2px var(--color-bg),
			0 0 2px var(--color-bg);
		width: 70ch;
		transform-origin: center;
		transform: translate(-50%, -50%);
	}

	.tooltip pre {
		margin: 0;
		white-space: pre-wrap;
	}

	.camera-controls {
		position: fixed;
		right: 1em;
		bottom: 1em;
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
		background-color: var(--color-bg);
		border: 1px solid var(--color-border);
		color: var(--color-text);
		display: flex;
		align-items: center;
		justify-content: center;
		user-select: none;
		backdrop-filter: blur(2px);
	}

	.camera-controls button:active {
		background-color: var(--color-border);
	}

	#graph {
		position: fixed;
		top: 0;
		left: 0;
		width: 100vw;
		height: 100vh;
	}

	#graph.has-renderer:active {
		cursor: move;
	}

	.env-warning {
		position: fixed;
		top: 50%;
		left: 50%;
		transform: translate(-50%, -50%);
		font-family: "Fantasque Sans Mono", monospace;
		opacity: 0.5;
		color: var(--color-text);
		background: var(--color-bg);
		max-width: 50ch;
	}
</style>
