<script lang="ts">
	import type { DisplayNode } from "$lib/node"
	import { page } from "$app/state"
	import Graph from "./Graph.svelte"
	import SidebarNode from "./SidebarNode.svelte"
	import { date_time_fmt } from "$lib/date"
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

	let sidebar_nodes_element = $state<HTMLElement | null>(null)
	let button = $state("/button.png")
	let embed_node = $state(nodes?.[0])

	const init_at = nodes.find(
		(n) => n.url_param === page.url.searchParams.get("node")
	)?.at
	const highlighted_node = $derived(browser ? page.state.node : init_at)

	const snippet = $derived(
		`<a href="${page.url.origin}?${new URLSearchParams({ node: embed_node.url_param })}" rel="external">` +
			`<img src="${new URL(button, page.url.origin).href}" style="image-rendering: pixelated;" height="31" width="88"/>` +
			`</a>`
	)

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
			A <a href="/doc/spec.md">webchain</a>
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
			See the <a href="/doc/manual.md">manual page</a>
			for more information.
		</p>
	</details>

	<details name="qna">
		<summary>socialize</summary>
		<p>
			If you want to link to this webchain from your site, an old-web style
			button can be created with this form:
		</p>
		<form>
			<label for="button-style">Style</label>
			<br />
			<label class="button-option">
				<input
					type="radio"
					name="button-style"
					value="/button.png"
					bind:group={button}
				/>
				<img
					src="/button.png"
					class="button"
					height="31"
					width="88"
					alt="An old-web style button with the webchain's logo on the right, with some pixel-art chains to the left. This one is more monochrome."
				/>
			</label>
			<label class="button-option">
				<input
					type="radio"
					name="button-style"
					value="/button2.png"
					bind:group={button}
				/>
				<img
					src="/button2.png"
					class="button"
					height="31"
					width="88"
					alt="An old-web style button with the webchain's logo on the right, with some pixel-art chains to the left. This one is tinted more blue."
				/>
			</label>
			{#if browser}
				<br />
				<label for="links-to">Links to</label>
				<select
					name="links-to"
					onchange={(e) => {
						const select = e.currentTarget as HTMLSelectElement
						const at = select.value
						const node = nodes.find((n) => n.at === at)
						if (node == null) return

						embed_node = node
					}}
				>
					{#each nodes as node (node.at)}
						<option value={node.at}>{node?.label}</option>
					{/each}
				</select>
			{/if}
			<br />
			<label>
				Snippet to include on your site<br /><input
					type="text"
					readonly
					value={snippet}
					onmouseup={(e) => {
						e.currentTarget.select()
					}}
				/>
			</label>
		</form>
		<p>
			The <code>?node</code> query parameter can be used to highlight a specific
			node in the webchain.
		</p>
	</details>

	<details name="qna">
		<summary>user group</summary>
		<p>
			If you are a member or prospective member, you can come chat in the <a
				href="https://irc.milkmedicine.net"
				rel="external">#webchain channel on irc.milkmedicine.net</a
			>. You may also send an email to
			<a href="mailto:meri@himawari.fun?subject=webchain inquiry"
				>meri@himawari.fun</a
			> if you have a private inquiry.
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

	form {
		border: double var(--color-border);
		padding: 0.5rem;
	}

	.button-option {
		display: inline-flex;
		align-items: center;
		gap: 0.25rem;
	}

	select {
		font-family: "Fantasque Sans Mono", monospace;
		font-size: 0.9rem;
		padding: 0.25em;
		border: 1px solid var(--color-border);
		background: var(--color-bg);
		color: var(--color-text);
		width: 100%;
		max-width: 14rem;
	}

	input[type="text"] {
		font-family: "Fantasque Sans Mono", monospace;
		font-size: 0.9rem;
		width: 100%;
		max-width: 14rem;
		padding: 0.25em;
		border: 1px solid var(--color-border);
		background: var(--color-bg);
		box-sizing: border-box;
		color: var(--color-text);
	}

	label {
		margin: 0.5rem 0;
	}
</style>
