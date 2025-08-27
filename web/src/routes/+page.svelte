<script lang="ts">
	import { onMount } from "svelte"

	let graph_element: HTMLElement

	onMount(() => {
		let sigmaInstance: any

		const initGraph = async () => {
			const { default: Graph } = await import("graphology")
			const { default: Sigma } = await import("sigma")

			const graph = new Graph()
			graph.addNode("1", { label: "Node 1", size: 10, color: "blue" })
			graph.addNode("2", { label: "Node 2", size: 20, color: "red" })
			graph.addNode("3", { label: "Node 2", size: 20, color: "red" })
			graph.addNode("4", { label: "Node 2", size: 20, color: "red" })

			graph.addEdge("1", "2", { size: 5, color: "purple" })
			graph.addEdge("1", "3", { size: 5, color: "purple" })
			graph.addEdge("1", "4", { size: 5, color: "purple" })


			graph.nodes().forEach((node, i) => {
				const angle = (i * 2 * Math.PI) / graph.order
				graph.setNodeAttribute(node, "x", 100 * Math.cos(angle))
				graph.setNodeAttribute(node, "y", 100 * Math.sin(angle))
			})
			sigmaInstance = new Sigma(graph, graph_element)
		}

		initGraph()

		return () => {
			if (sigmaInstance) {
				sigmaInstance.kill()
			}
		}
	})
</script>

<svelte:head>
	<link rel="webchain" href="https://webchain.milkmedicine.net" />
	<link rel="webchain-nomination" href="https://www.himawari.fun/" />
	<link rel="webchain-nomination" href="https://nekopath.fun/" />
</svelte:head>

<h1>milkmedicine webchain</h1>
<p>there will be a thing to visualize the webchain here soon</p>
<div id="graph" bind:this={graph_element}></div>

<style>
	#graph {
		width: 600px;
		height: 600px;
	}
</style>
