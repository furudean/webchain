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
</svelte:head>

<Graph nodes={data.nodes}></Graph>


<main>
	<h1>milkmedicine webchain</h1>
	<p>
		<a href="https://github.com/furudean/webchain/blob/main/SPEC.md" rel="external">webchain</a> is a distributed webring, where each member website can nominate
		other websites, creating a walkable graph of trust.
	</p>
	<ol>
		<li>
			This page is the starting point of the <em>webchain</em>, nominating three other websites
		</li>
		<li>
			Nominated websites can add their own nominations by adding markup to their HTML
		</li>
		<li>Each nominated node may nominate three others</li>
		<li>
			And so on, and so forth,
		</li>

	</ol>
	{#if !data.nodes}
		<p>something is broken</p>
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
