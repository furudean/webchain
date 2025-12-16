<script lang="ts">
	import { date_time_fmt } from "$lib/date"
	import type { PageProps } from "./$types"
	import Node from "./Node.svelte"

	let { data }: PageProps = $props()

	const sorted_nodes = $derived(
		data.nodes.toSorted((a, b) => a.label.localeCompare(b.label, "en"))
	)
</script>

<svelte:head>
	<title>gallery · milkmedicine webchain</title>
</svelte:head>

<h1>gallery</h1>

{#if data.nodes.length > 0}
	<ul>
		{#each sorted_nodes as node}
			<Node {node} parent_node={data.nodes.find((n) => node.parent === n.at)}
			></Node>
		{/each}
	</ul>
{/if}
{#if data.end}
	<p>
		<a href="/crawler/current.json" class="crawl-info">
			last crawled <time datetime={data.end.toISOString()}
				>{date_time_fmt.format(data.end).toLowerCase()}</time
			>
		</a>
	</p>
{/if}

<style>
	ul {
		display: grid;
		grid-template-columns: repeat(auto-fit, minmax(20rem, 1fr));
		gap: 2rem 1rem;
		padding: 0;
		list-style: none;
	}
</style>
