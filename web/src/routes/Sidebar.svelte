<script lang="ts">
	import type { DisplayNode } from "$lib/node"
	import { page } from "$app/state"
	import Graph from "./Graph.svelte"
	import SidebarNode from "./SidebarNode.svelte"
	import { date_time_fmt } from "$lib/date"
	import { last_visited } from "$lib/visited"
	import { browser } from "$app/environment"

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

	// if server-side, initialize highlighted_node from URL param
	const init_at = nodes.find(
		(n) => n.url_param === page.url.searchParams.get("node")
	)?.at
	const highlighted_node = $derived(browser ? page.state.node : init_at)
	const highlighted_node_cls = $derived.by(() => {
		if (highlighted_node) {
			return nodes.find((n) => n.at === highlighted_node) ?? null
		}
		return null
	})

	let sidebar_nodes_element = $state<HTMLElement | null>(null)

	const snippet = `
		<a href="${page.url.href}" rel="external"><img
			src="${new URL("/button.png", page.url.origin).href}"
			style="image-rendering: pixelated;"
			height="31"
			width="88"
		/></a>`
		.replace(/\s+/g, " ")
		.trim()

	const recent_nodes = $derived.by(() => {
		const newest_timestamp = Math.max(
			...nodes.map((n) => n.first_seen?.getTime() ?? 0)
		)
		if (!newest_timestamp) return []

		if ($last_visited instanceof Date) {
			const cutoff = $last_visited.getTime() - 1000 * 60 * 60 * 6 // 6 hours
			const recent = nodes.filter(
				(node) => (node.first_seen?.getTime() ?? 0) > cutoff
			)
			return recent.map((n) => n.at)
		} else {
			const now = new Date().getTime()
			const cohort_window = 1000 * 60 * 60 * 24 * 3 // 2 days
			const stale_threshold = 1000 * 60 * 60 * 24 * 14 // 2 weeks

			if (now - newest_timestamp > stale_threshold) {
				return []
			}

			return nodes
				.filter((node) => {
					const first_seen = node.first_seen?.getTime() ?? 0
					return first_seen > newest_timestamp - cohort_window
				})
				.map((n) => n.at)
		}
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
</script>

<aside class:open={highlighted_node} aria-label="Sidebar">
	<h1>
		<span class="square" aria-hidden="true"></span> the<br />milkmedicine<br
		/>webchain
	</h1>

	<p>a distributed webring for friends and enemies</p>

	<details name="qna">
		<summary>webchain?</summary>
		<p>
			A <a href="/spec">webchain</a>
			is a distributed
			<a href="https://en.wikipedia.org/wiki/Webring" rel="external">webring</a
			>, where each tracked website can nominate new members, creating a
			walkable graph of trust.
		</p>

		<ol>
			<li>
				This page is the starting point of the <em>milkmedicine webchain</em>,
				which is itself a webchain link. It nominates several other websites in
				its HTML.
			</li>
			<li>
				Nominated websites may add nominations by adding markup to their HTML,
				up to a limit of {nominations_limit}.
			</li>
			<li>
				Those websites may nominate {nominations_limit} others, and so on, and so
				forth.
			</li>
		</ol>

		<p>
			A crawler visits each link, reads its nominations, and then visits those
			links recursively, building up a graph of all reachable sites. The crawler
			runs periodically, so new links will appear on this page over time.
		</p>
		<p>
			Source code may be found <a
				href="https://github.com/furudean/webchain"
				rel="external">on GitHub</a
			>.
		</p>
	</details>

	<details name="qna">
		<summary>nomination</summary>
		<p>
			To nominate new pages to the webchain, an existing member can add markup
			to its HTML, for example:
		</p>
		<pre><code
				>&lt;-- https://example.org ---&gt;
&lthtml&gt;
&lt;head&gt;
	&lt;link rel="webchain"
		href="{page.url.origin}" /&gt;
	&lt;link rel="webchain-nomination"
		href="https://foo.bar" /&gt;
&lt;/head&gt;
&lt;body&gt;
	...
&lt/body&gt;
&lt/html&gt;</code
			></pre>
		<p>
			This snippet shows the website <code>https://example.org</code>. This site
			nominates
			<code>https://foo.bar</code>
			to be part of the webchain
			<code>{page.url.origin}</code>.
		</p>
		<blockquote>
			The <code>webchain</code> link points to the webchain the website wants to
			be a part of. The
			<code>webchain-nomination</code> links point to up to {nominations_limit} other
			websites that this node nominates.
		</blockquote>
		<p>
			<b>Note</b>: A website must first be a member of the webchain via
			nomination before it can appear on the graph.
		</p>
	</details>

	<details name="qna">
		<summary>socialize</summary>
		<p>
			If you want to link to this webchain from your site, an old-web style
			button is provided below.
		</p>
		<p>
			<img
				src="button.png"
				class="button"
				height="31"
				width="88"
				alt="An old-web style button with the webchain's logo on the right, with some pixel-art chains to the left."
			/>
		</p>
		<p>
			You can use the following HTML snippet to include it on your site: <input
				type="text"
				readonly
				value={snippet}
				onclick={(e) => {
					e.currentTarget.select()
				}}
			/>
		</p>

		<p></p>
		<p>
			The <code>?node</code> query parameter can be used to highlight a specific
			node in the webchain, like:
		</p>
		<pre><code
				>{highlighted_node
					? page.url.href
					: page.url.origin + "?node=" + nodes.at(1)?.url_param}</code
			></pre>
	</details>

	<details name="qna">
		<summary>questions</summary>
		<p>
			If you have inquiries (including wanting to join this webchain), you can
			come chat in the <a href="https://irc.milkmedicine.net" rel="external"
				>#webchain channel on irc.milkmedicine.net</a
			>. You may also send an email to
			<a href="mailto:meri@himawari.fun?subject=webchain inquiry"
				>meri@himawari.fun</a
			>.
		</p>
	</details>
	<h2>sites</h2>
	<p>
		{new Intl.NumberFormat("en-US").format(nodes.length)} links in this webchain
	</p>
	{#if nodes.length > 0}
		<ul class="nodes" bind:this={sidebar_nodes_element}>
			<SidebarNode
				at={nodes[0].at}
				{nodes}
				{highlighted_node}
				{nominations_limit}
				{graph_component}
				{recent_nodes}
			/>
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

	summary {
		margin: 0;
	}

	details {
		max-width: 40ch;
	}

	details > :nth-child(2) {
		margin-top: 0;
	}

	[name="qna"] {
		padding: 0 0.5rem;
		border: 1px solid transparent;
	}

	[name="qna"]:has(> :focus-visible) {
		outline: 2px solid var(--color-primary);
	}

	[name="qna"] summary:focus {
		outline: none;
	}

	[name="qna"]:is(:hover, :focus-visible) {
		border: 1px dashed var(--color-text);
	}

	[name="qna"][open] {
		border: 1px dashed var(--color-text);
		background: var(--color-solid);
	}

	[name="qna"] summary {
		padding: 0.5rem 0;
		font-style: italic;
	}

	[name="qna"] ol li {
		margin: 0.5rem 0;
	}

	ul {
		margin: 0;
		padding: 0;
	}

	.nodes {
		margin-top: 1rem;
	}

	pre {
		overflow-x: auto;
	}

	.button {
		image-rendering: pixelated;
		image-rendering: crisp-edges;
		max-width: 100%;
		height: auto;
	}

	.crawl-info {
		display: block;
		font-size: 0.8rem;
		color: var(--color-shy);
		margin: 2rem 0;
	}

	input[type="text"] {
		font-family: "Fantasque Sans Mono", monospace;
		font-size: 0.9rem;
		min-width: 15rem;
		padding: 0.25em;
		border: 1px solid var(--color-border);
		background: none;
		box-sizing: border-box;
		color: var(--color-text);
	}
</style>
