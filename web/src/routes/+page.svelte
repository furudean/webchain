<script lang="ts">
	import type { PageProps } from "./$types"
	import Graph from "./Graph.svelte"
	import Sidebar from "./Sidebar.svelte"

	let highlighted_node: string | undefined = $state()
	let hovered_node: string | undefined = $state()

	let { data }: PageProps = $props()
</script>

<svelte:head>
	<link rel="webchain" href="https://webchain.milkmedicine.net" />
	<link rel="webchain-nomination" href="https://www.himawari.fun/" />
	<link rel="webchain-nomination" href="https://nekopath.fun/" />
	<link rel="webchain-nomination" href="https://eidoli.ca" />
	<title>milkmedicine webchain</title>
</svelte:head>

<div class="container">
	<Graph nodes={data.nodes} bind:highlighted_node bind:hovered_node></Graph>
	<!-- <Sidebar data.start={data.data.start} data.end={data.data.end}></Sidebar> -->
	<Sidebar
		nodes={data.nodes}
		bind:highlighted_node
		bind:hovered_node
	></Sidebar>

	{#if data.start && data.end}
		<span>
			last crawled at {new Date(data.start).toLocaleString("en-US").toLowerCase()}, took {Math.round((data.end.getTime() - data.start.getTime()) / 1000)} seconds
		</span>
	{/if}
</div>

<style>
	.container {
		position: relative;
		/* display: grid; */
		/* grid-template-areas: "sidebar graph";
		grid-template-columns: 1fr 2fr;
		width: 100%;
		min-height: 100vh; */
	}

	span {
		position: fixed;
		bottom: 0;
		right: 0;
		font-size: 0.9rem;
		color: #666;
		padding: 0.4em;
		pointer-events: none;
	}
</style>
