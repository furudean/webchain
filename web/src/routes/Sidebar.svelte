<script lang="ts">
	import type { DisplayNode } from "$lib/node"
	import { page } from "$app/state"
	import Graph from "./Graph.svelte"
	import SidebarNode from "./SidebarNode.svelte"
	import { date_time_fmt } from "$lib/date"
	import { browser } from "$app/environment"
	import { goto } from "$app/navigation"
	import QnA from "./QnA.svelte"

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

	const init_at = nodes.find(
		(n) => n.url_param === page.url.searchParams.get("node")
	)?.at
	const highlighted_node = $derived(browser ? page.state.node : init_at)

	const recent_nodes = $derived.by(() => {
		const newest_timestamp = Math.max(
			...nodes.map((n) => n.first_seen?.getTime() ?? 0)
		)
		if (!newest_timestamp) return []

		const now = new Date().getTime()
		const cohort_window = 1000 * 60 * 60 * 24 * 3.5 // 3.5 days
		const stale_threshold = 1000 * 60 * 60 * 24 * 7 // 7 days

		if (now - newest_timestamp > stale_threshold) {
			return []
		}

		return nodes
			.filter(
				(node) =>
					(node.first_seen?.getTime() ?? 0) > newest_timestamp - cohort_window
			)
			.map((n) => n.at)
	})

	const sorts = [
		{ key: "tree", value: "webchain" },
		{ key: "new", value: "newest" },
		{ key: "old", value: "oldest" },
		{ key: "asc", value: "url(↓)" },
		{ key: "desc", value: "url(↑)" }
	] as const
	const current_sort: (typeof sorts)[number] = $derived.by(() => {
		const param = page.url.searchParams.get("sort")

		const found = sorts.find((sort) => sort.key === param)
		if (found) return found

		return sorts[0]
	})

	function node_sort(type: "new" | "old" | "asc" | "desc") {
		switch (type) {
			case "new":
				return (a: DisplayNode, b: DisplayNode) =>
					(b.first_seen?.getTime() ?? 0) - (a.first_seen?.getTime() ?? 0)
			case "old":
				return (a: DisplayNode, b: DisplayNode) =>
					(a.first_seen?.getTime() ?? 0) - (b.first_seen?.getTime() ?? 0)
			case "asc":
				return (a: DisplayNode, b: DisplayNode) =>
					(a.label ?? "").localeCompare(b.label ?? "", "en-US")
			case "desc":
				return (a: DisplayNode, b: DisplayNode) =>
					(b.label ?? "").localeCompare(a.label ?? "", "en-US")
			default:
				return () => 0
		}
	}

	function url_with_sort(type: string): string {
		const params = new URLSearchParams(page.url.searchParams)

		if (type === "tree") {
			params.delete("sort")
		} else {
			params.set("sort", type)
		}

		return params.keys() ? "?" + params.toString() : ""
	}

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
</script>

<aside class:open={highlighted_node} aria-label="Sidebar">
	<h1>
		<span class="square" aria-hidden="true"></span> the<br />milkmedicine<br
		/>webchain
	</h1>

	<p style="max-width: 20rem">a distributed webring for friends and enemies</p>

	<QnA {nodes} {nominations_limit}></QnA>

	<h2>pages</h2>
	<div class="sorts">
		{new Intl.NumberFormat("en-US").format(nodes.length)} links ·
		{#if browser}
			<!-- if javascript, we can do whatever we want \o/ -->
			<label for="sort">ordered by</label>
			<select
				id="sort"
				aria-label="Sort nodes"
				onchange={(e) => {
					const select = e.currentTarget as HTMLSelectElement
					goto(url_with_sort(select.value), {
						replaceState: true,
						noScroll: true,
						keepFocus: true,
						state: { node: highlighted_node }
					})
				}}
			>
				{#each sorts as sort_option}
					<option
						value={sort_option.key}
						selected={sort_option === current_sort}
					>
						{sort_option.value}
					</option>
				{/each}
			</select>
		{:else}
			<!-- if server rendered only, selects can't do actions on change. links still work -->
			<div class="chips">
				ordered by
				{#each sorts as sort_option}
					<a
						href={url_with_sort(sort_option.key)}
						aria-current={sort_option === current_sort ? "page" : undefined}
						>{sort_option.value}</a
					>
				{/each}
			</div>
		{/if}
	</div>

	{#if nodes.length > 0}
		<ul id="nodes" bind:this={sidebar_nodes_element}>
			{#if current_sort.key === "tree"}
				<!-- List as tree -->
				<SidebarNode
					at={nodes[0].at}
					{nodes}
					{highlighted_node}
					{nominations_limit}
					{graph_component}
					{recent_nodes}
					render_children={true}
				/>
			{:else}
				<!-- List is flat list -->
				{#each [...nodes].sort(node_sort(current_sort.key)) as node (node.at)}
					<SidebarNode
						at={node.at}
						{nodes}
						{highlighted_node}
						{nominations_limit}
						{graph_component}
						{recent_nodes}
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

	ul {
		margin: 0;
		padding: 0;
	}

	.chips {
		max-width: 20rem;
		display: inline-flex;
		flex-wrap: wrap;
		gap: 0.5ch;
		padding: 0;
		list-style-type: none;
	}

	.chips a {
		line-height: 1;
		display: inline-block;
		padding: 0.25em 0.5em;
		border: 1px solid var(--color-border);
		background-color: var(--color-bg-secondary);
		color: var(--color-text);
		text-decoration: none;
		font-size: 0.8rem;
	}

	.chips a[aria-current="page"] {
		border-color: var(--color-primary);
		background-color: var(--color-primary);
		color: var(--color-text-primary);
		font-weight: bold;
	}

	#nodes {
		margin: 0.5rem 0;
	}

	p {
		margin: 0.5rem 0;
	}

	.crawl-info {
		display: block;
		font-size: 0.8rem;
		color: var(--color-shy);
		margin: 2rem 0;
	}
</style>
