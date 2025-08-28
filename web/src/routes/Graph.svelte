<script lang="ts">
	import { onMount } from "svelte"
	import raw_data from "./example-data-2.json?raw"
	import type { Sigma } from "sigma"
	import { calculateTreeLayout, buildGraph, type Node } from "$lib/graph"

	const data: Node[] = JSON.parse(raw_data)

	let graph_element: HTMLElement

	onMount(() => {
		let sigma_instance: Sigma | undefined

		const init_graph = async () => {
			const { default: Sigma } = await import("sigma")
			const { NodeImageProgram } = await import("@sigma/node-image")
			const { default: Graph } = await import("graphology")

			const hashmap = new Map(
				Object.values(data).map((node, i) => [i.toString(), node])
			)

			// Calculate layout and build graph
			const positions = calculateTreeLayout(hashmap)
			const graph = buildGraph(hashmap, positions, Graph)
			// Create Sigma instance
			sigma_instance = new Sigma(graph, graph_element, {
				nodeProgramClasses: {
					image: NodeImageProgram
				},
				labelRenderedSizeThreshold: 10, // Only show labels when significantly zoomed in
				labelSize: 10
			})

			// Set default zoom to be more zoomed out
			sigma_instance.getCamera().setState({
				ratio: 1.2
			})
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
	}

	:global(body) {
		background-size: 100px 100px;
		background-image:
			linear-gradient(to right, hsl(0, 0%, 95%) 1px, transparent 1px),
			linear-gradient(to bottom, hsl(0, 0%, 95%) 1px, transparent 1px);
	}
</style>
