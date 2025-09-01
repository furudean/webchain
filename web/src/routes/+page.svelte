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

<div class="container">
	<aside>
		<h1>milkmedicine webchain</h1>
		<p>
			a <a
				href="https://github.com/furudean/webchain/blob/main/SPEC.md"
				rel="external">webchain</a
			>
			is a distributed
			<a href="https://en.wikipedia.org/wiki/Webring" rel="external">webring</a
			>, where each member can nominate other websites, creating a walkable
			graph of trust.
		</p>
		<p>
			The current state of the <em>milkmedicine webchain</em> is visualized on this
			page. It's still in development... so please be nice.
		</p>
		<ol>
			<li>
				This page is the starting point of the <em>milkmedicine webchain</em>,
				which nominates three other websites
			</li>
			<li>
				Nominated websites may add their own nominations by adding markup to
				their HTML, up to a limit of three.
			</li>
			<li>
				Those websites may nominate three others, and so on, and so forth.
			</li>
		</ol>
		{#if data.nodes.length === 0}
			<p>However, something went wrong, as no nodes were found :(</p>
		{:else if data.start && data.end}
			The last crawl was {new Date(data.end)
				.toLocaleString("en-US")
				.toLowerCase()}, which took {(new Date(data.end).getTime() -
				new Date(data.start).getTime()) /
				1000} seconds
		{/if}
	</aside>
	<Graph nodes={data.nodes}></Graph>
</div>

<style>
	.container {
		display: grid;
		grid-template-areas: "aside graph";
		grid-template-columns: 1fr 2fr;
		width: 100vw;
		height: 100vh;
	}
	aside {
		grid-area: aside;
		max-width: 50ch;
		position: relative;
		z-index: 1;
		padding: 0 1rem;
	}
</style>
