<script lang="ts">
	import type { PageProps } from "./$types"
	import Graph from "./Graph.svelte"
	import Sidebar from "./Sidebar.svelte"

	let { data }: PageProps = $props()
	let graph_component: Graph | undefined = $state()
</script>

<svelte:head>
	<!-- common webchain metadata -->
	<link rel="webchain" href="https://webchain.milkmedicine.net" />
	<link rel="webchain-nomination" href="https://irc.milkmedicine.net/" />
	<link rel="webchain-nomination" href="https://www.himawari.fun/" />
	<link rel="webchain-nomination" href="https://nekopath.fun/" />
	<link rel="webchain-nomination" href="https://eidoli.ca" />

	<!-- set the nominations limit for each node - root only -->
	<meta name="webchain-nominations-limit" content="4" />

	<title>milkmedicine webchain</title>
	<meta
		name="description"
		content="a distributed webring for friends and enemies. you are here!"
	/>
	<meta name="theme-color" content="#0000ff" />
</svelte:head>

<div class="container">
	<Graph nodes={data.nodes} bind:this={graph_component}></Graph>
	<Sidebar
		nodes={data.nodes}
		{graph_component}
		nominations_limit={data.nominations_limit}
	></Sidebar>

	{#if data.start && data.end}
		<a href="/crawler/data.json">
			last crawled <time datetime={data.start.toISOString()}
				>{new Date(data.start).toLocaleString("en-US").toLowerCase()}</time
			>, taking {Math.round((data.end.getTime() - data.start.getTime()) / 1000)}
			seconds
		</a>
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

	a {
		position: fixed;
		bottom: 0;
		right: 0;
		font-size: 0.8rem;
		color: #666;
		padding: 0.4em;
	}
</style>
