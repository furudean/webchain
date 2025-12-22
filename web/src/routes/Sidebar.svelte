<script lang="ts">
	import type { DisplayNode } from "$lib/node"
	import { page } from "$app/state"
	import Graph from "./Graph.svelte"
	import SidebarNode from "./SidebarNode.svelte"
	import { date_time_fmt } from "$lib/date"
	import { browser } from "$app/environment"
	import QnA from "./QnA.svelte"
	import SelectSort, { type Sort } from "$lib/SelectSort.svelte"

	let {
		nodes = [],
		nominations_limit = -1,
		crawl_date,
		graph_component
	}: {
		nodes: DisplayNode[]
		nominations_limit: number | null
		crawl_date: Date | null
		graph_component: Graph
	} = $props()

	let sidebar_nodes_element = $state<HTMLElement | null>(null)

	// svelte-ignore state_referenced_locally
	const init_at = nodes.find(
		(n) => n.url_param === page.url.searchParams.get("node")
	)?.at
	let highlighted_node = $derived(browser ? page.state.node : init_at)

	const sorts: Sort[] = [
		{ key: "tree", value: "nomination", fn: () => 0 },
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
			key: "asc",
			value: "alphabetic (↓)",
			fn: (a: DisplayNode, b: DisplayNode) =>
				(a.label ?? "").localeCompare(b.label ?? "", "en-US")
		},
		{
			key: "desc",
			value: "alphabetic (↑)",
			fn: (a: DisplayNode, b: DisplayNode) =>
				(b.label ?? "").localeCompare(a.label ?? "", "en-US")
		}
	]

	let sort_value = $state(page.url.searchParams.get("sort"))

	const current_sort = $derived.by(() => {
		const found = sorts.find((sort) => sort.key === sort_value)
		if (found) return found

		return sorts[0]
	})

	$effect(() => {
		if (highlighted_node) {
			const open_node = sidebar_nodes_element?.querySelector(
				`details[open]`
			) as HTMLElement | null
			open_node?.scrollIntoView({ block: "nearest" })
			open_node?.querySelector("summary")?.focus({
				preventScroll: true
			})
		}
	})

	let page_url = $state(page.url)

	$effect(() => {
		// if updated externally
		const param = page_url.searchParams.get("sort")
		sort_value = param
	})
</script>

<aside class:open={highlighted_node} aria-label="Sidebar">
	<h1>
		<span class="square" aria-hidden="true"></span> the<br />milkmedicine<br
		/>webchain
	</h1>

	<p class="limit-len">a distributed webring for friends and enemies</p>

	<nav>
		<ul>
			<li>
				<a href="/gallery">/gallery</a>
			</li>
			<li>
				<a href="/doc">/docs</a>
			</li>
		</ul>
	</nav>

	<QnA {nodes} {nominations_limit}></QnA>

	<div class="sorts limit-len">
		{new Intl.NumberFormat("en-US").format(nodes.length)} links
		<span class="sep">·</span>
		<SelectSort bind:sort_value {sorts}></SelectSort>
	</div>

	{#if nodes.length > 0}
		<ul id="nodes" bind:this={sidebar_nodes_element}>
			{#if current_sort.key === "tree"}
				<!-- Use recursion via render_children -->
				<SidebarNode
					at={nodes[0].at}
					{nodes}
					{highlighted_node}
					{nominations_limit}
					{graph_component}
					render_children={true}
				/>
			{:else}
				<!-- List is flat -->
				{#each nodes.toSorted(current_sort.fn) as node (node.at)}
					<SidebarNode
						at={node.at}
						{nodes}
						{highlighted_node}
						{nominations_limit}
						{graph_component}
						render_children={false}
					/>
				{/each}
			{/if}
		</ul>
	{/if}

	{#if crawl_date}
		<a href="/crawler/current.json" class="crawl-info">
			last crawled <time datetime={crawl_date.toISOString()}
				>{date_time_fmt.format(crawl_date).toLowerCase()}</time
			>
		</a>
	{/if}
</aside>

<style>
	aside {
		position: absolute;
		top: 0;
		left: 0;
		padding: 0 1rem;
		background: linear-gradient(to right, var(--color-bg), transparent);
		min-height: 100vh;
		will-change: backdrop-filter;
		color: var(--color-text);
	}

	.square {
		display: inline-block;
		width: 1.1em;
		height: 1.1em;
		background: var(--color-primary);
		margin-right: 0.1em;
		vertical-align: sub;
	}

	@media (max-width: 35rem) {
		aside {
			border-right: 1px solid var(--color-border, rgba(0, 0, 0, 0.25));
			background: linear-gradient(to right, var(--color-bg), transparent);
			backdrop-filter: blur(1.5px);
			transform: translateX(-90%);
			transition: transform 200ms ease-in-out;
			max-width: calc(100vw - 6rem);
		}
		aside.open,
		aside:hover {
			transform: translateX(0%);
		}
	}

	aside:hover {
		border-right: 1px solid var(--color-border, rgba(0, 0, 0, 0.25));
		background: linear-gradient(to right, var(--color-bg), transparent);
		backdrop-filter: blur(1.5px);
	}

	.sorts {
		margin: 1rem 0;
		line-height: 1;
	}

	ul {
		margin: 0;
		padding: 0;
	}

	#nodes {
		margin: 0.5rem 0;
	}

	.crawl-info {
		display: block;
		font-size: 0.8rem;
		color: var(--color-shy);
		margin: 2rem 0;
	}

	.limit-len {
		max-width: 20rem;
	}

	nav ul {
		display: flex;
		gap: 1rem;
		list-style-type: none;
		margin: 1rem 0;
	}

	nav :any-link {
		color: var(--color-primary);
	}

	nav ul li {
		display: inline-block;
	}
</style>
