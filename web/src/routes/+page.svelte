<script lang="ts">
	import type { PageProps } from "./$types"
	import Graph from "./Graph.svelte"
	import Sidebar from "./Sidebar.svelte"

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
	<Graph nodes={data.nodes}></Graph>
	<Sidebar start={data.start} end={data.end}></Sidebar>
</div>

<style>
	.container {
		display: grid;
		grid-template-areas: "aside graph";
		grid-template-columns: 1fr 2fr;
		width: 100vw;
		height: 100vh;
	}
</style>
