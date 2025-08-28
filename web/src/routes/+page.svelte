<script lang="ts">
	import type { PageProps } from "./$types"
	import Graph from "./Graph.svelte"

	let { data }: PageProps = $props()
</script>

<svelte:head>
	<link rel="webchain" href="https://webchain.milkmedicine.net" />
	<link rel="webchain-nomination" href="https://www.himawari.fun/" />
	<link rel="webchain-nomination" href="https://nekopath.fun/" />
	<link rel="webchain-nomination" href="https://eidoli.ca" />
	<title>milkmedicine webchain</title>
</svelte:head>

<Graph nodes={data.nodes}></Graph>


<main>
	<h1>milkmedicine webchain</h1>
	<p>
		a <a href="https://github.com/furudean/webchain/blob/main/SPEC.md" rel="external">webchain</a> is a distributed webring, where each member can nominate
		other websites, creating a walkable graph of trust.
	</p>
	<ol>
		<li>
			This page is the starting point of the <em>milkmedicine webchain</em>, which nominates three other websites
		</li>
		<li>
			Nominated websites can add their own nominations by adding markup to their HTML
		</li>
		<li>Each nominated node may nominate three others</li>
		<li>
			And so on, and so forth,
		</li>

	</ol>
	{#if data.nodes.length === 0}
		<p>however, something is wrong, as no nodes were found :(</p>
	{:else if data.timestamp}
		last crawl was {new Date(data.timestamp).toLocaleString('en-US').toLowerCase()}
	{/if}
</main>




<style>
	main {
		max-width: 60ch;
		position: relative;
		z-index: 1;
	}
</style>
