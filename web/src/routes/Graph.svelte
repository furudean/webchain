<script lang="ts">
	import { onMount } from "svelte"
	import type { Sigma, Camera } from "sigma"
	import { calculateTreeLayout, buildGraph } from "$lib/graph"
	import type { Node } from "$lib/node"

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
		let sigma_instance: Sigma | undefined

		const init_graph = async () => {
			const { default: Sigma } = await import("sigma")
			const { NodeImageProgram } = await import("@sigma/node-image")
			const { default: Graph } = await import("graphology")
			const { NodeSquareProgram } = await import("@sigma/node-square")

			const hashmap = new Map(
				Object.values(nodes).map((node, i) => [i.toString(), node])
			)

			const positions = calculateTreeLayout(hashmap)
			const graph = buildGraph(hashmap, positions, Graph)
			sigma_instance = new Sigma(graph, graph_element, {
				nodeProgramClasses: {
					image: NodeImageProgram,
					square: NodeSquareProgram
				},
				labelRenderedSizeThreshold: 14,
				labelSize: 10,
				maxCameraRatio: 3,
				minCameraRatio: 0.75
			})

			const camera = sigma_instance.getCamera()
			camera.setState({
				ratio: 1.2
			})
			camera.addListener("updated", update_camera)
			update_camera(camera)
		}

		init_graph().catch(console.error)

		return () => {
			if (sigma_instance) {
				sigma_instance.kill()
			}
		}
	})
</script>

<div id="graph" bind:this={graph_element}></div>

<style>
	#graph {
		width: 100vw;
		height: 100vh;
		position: fixed;
		top: 0;
		left: 0;
		background-image:
			linear-gradient(to right, hsl(0, 0%, 95%) 1px, transparent 1px),
			linear-gradient(to bottom, hsl(0, 0%, 95%) 1px, transparent 1px);
		background-size: 83.3333px 83.3333px;
		background-position: 8.33333% 91.6667%;
		background-origin: 0 0;
	}
</style>
