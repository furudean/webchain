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

<h1>milkmedicine webchain</h1>
<p>there will be a thing to visualize the webchain here soon</p>
<Graph nodes={data.nodes}></Graph>
