<script lang="ts">
	import { page } from "$app/state"
	import { date_time_fmt } from "$lib/date"
	import type { DisplayNode } from "$lib/node"
	import SelectSort, { type Sort } from "$lib/SelectSort.svelte"
	import type { PageProps } from "./$types"
	import Node from "./Node.svelte"

	let { data }: PageProps = $props()

	let grid_size = $state(300)

	const sorts: Sort[] = [
		// { key: "tree", value: "nomination", fn: () => 0 },
		{
			key: "new",
			value: "newest",
			fn: (a: DisplayNode, b: DisplayNode) =>
				(b.first_seen?.getTime() ?? 0) - (a.first_seen?.getTime() ?? 0)
		},
		{
			key: "old",
			value: "oldest",
			fn: (a: DisplayNode, b: DisplayNode) =>
				(a.first_seen?.getTime() ?? 0) - (b.first_seen?.getTime() ?? 0)
		},
		{
			key: "url",
			value: "url",
			fn: (a: DisplayNode, b: DisplayNode) =>
				(a.label ?? "").localeCompare(b.label ?? "", "en-US")
		}
	]

	let sort_value = $state(page.url.searchParams.get("sort"))

	const current_sort = $derived.by(() => {
		const found = sorts.find((sort) => sort.key === sort_value)
		if (found) return found

		return sorts[0]
	})

	const sorted_nodes = $derived(data.nodes.toSorted(current_sort.fn))
</script>

<svelte:head>
	<title>gallery · milkmedicine webchain</title>
</svelte:head>

<h1>gallery</h1>

<div class="sorts limit-len">
	{new Intl.NumberFormat("en-US").format(data.nodes.length)} links
	<span class="sep">·</span>
	<SelectSort bind:sort_value {sorts}></SelectSort>
</div>

<div class="scale">
	<input type="range" min="150" max="500" step="50" bind:value={grid_size} />
	<span>{grid_size}px</span>
</div>

{#if data.nodes.length > 0}
	<ul style:--grid-size="{grid_size}px">
		{#each sorted_nodes as node}
			<Node
				{node}
				parent_node={data.nodes.find((n) => node.parent === n.at)}
				children={data.nodes.filter((n) => node.children.includes(n.at))}
			></Node>
		{/each}
	</ul>
{/if}
{#if data.end}
	<hr />
	<p>
		<a href="/crawler/current.json" class="crawl-info">
			webchain last crawled on <time datetime={data.end.toISOString()}
				>{date_time_fmt.format(data.end).toLowerCase()}</time
			>
		</a>
	</p>
{/if}

<style>
	.sorts {
		float: left;
		margin: 1rem 0;
	}

	.scale {
		float: right;
		margin: 1rem 0;
		font-family: "Fantasque Sans Mono", monospace;
	}

	input[type="range"] {
		margin: 0;
		vertical-align: middle;
		width: 10em;
	}

	ul {
		clear: both;
		--grid-size: 20rem;
		display: grid;
		grid-template-columns: repeat(auto-fit, minmax(var(--grid-size), 1fr));
		gap: 2rem 1rem;
		padding: 0;
		list-style: none;
	}

	.crawl-info {
		font-size: 0.85em;
		opacity: 0.8;
		color: inherit;
	}
</style>
