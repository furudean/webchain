<script lang="ts">
	import type { DisplayNode } from "$lib/node"
	import { page } from "$app/state"
	import Graph from "./Graph.svelte"
	import SidebarNode from "./SidebarNode.svelte"

	let {
		nodes,
		nominations_limit,
		graph_component
	}: {
		nodes: DisplayNode[]
		nominations_limit: number | null
		graph_component: Graph
	} = $props()

	const highlighted_node = $derived(page.state.node)

	let node_components: Record<string, SidebarNode> = $state({})

	$effect(() => {
		if (highlighted_node === undefined) return
		const current_component = node_components[highlighted_node]
		if (!current_component) return
		current_component.scrollIntoView()
	})
</script>

<aside>
	<h1>
		<span class="square" aria-hidden="true"></span> the<br />milkmedicine<br
		/>webchain
	</h1>

	<p>a distributed webring for friends and enemies</p>

	<details class="qna" name="qna">
		<summary>what?</summary>
		<p>
			A <a href="/spec">webchain</a>
			is a distributed
			<a href="https://en.wikipedia.org/wiki/Webring" rel="external">webring</a
			>, where each member site can nominate other websites, creating a walkable
			graph of trust.
		</p>
		<p>
			The current state of the <em>milkmedicine webchain</em> is visualized on this
			page.
		</p>
		<ol>
			<li>
				This page is the starting point of the <em>milkmedicine webchain</em>,
				which is itself a webchain node. It nominates several other websites,
				which you can see below.
			</li>
			<li>
				Nominated websites may add their nominations by adding markup to their
				HTML, up to a limit of {nominations_limit}.
			</li>
			<li>
				Those websites may nominate {nominations_limit} others, and so on, and so
				forth.
			</li>
		</ol>
		<p>
			Source code can be found <a
				href="https://github.com/furudean/webchain"
				rel="external">on GitHub</a
			>.
		</p>
	</details>

	<details class="qna" name="qna">
		<summary>how?</summary>
		<p>
			To nominate the webchain, each member node adds markup to their HTML, for
			example:
		</p>
		<pre><code
				>&lthtml&gt;
&lt;head&gt;
  &lt;link rel="webchain"
    href="https://example.com" /&gt;
  &lt;link rel="webchain-nomination"
    href="https://another.example.com" /&gt;
  &lt;link rel="webchain-nomination"
    href="https://yetanother.example.com" /&gt;
&lt;/head&gt;
&lt;body&gt;
    ...
&lt/body&gt;
&lt/html&gt;</code
			></pre>
		<p>
			The <code>webchain</code> link points to root of the webchain the website
			wants to be a part of, in this case that would be
			<code>https://webchain.milkmedicine.net/</code>. The
			<code>webchain-nomination</code> links point to up to other websites that this
			node nominates.
		</p>
		<blockquote>
			Note that a node must first be nominated by the webchain before it can add
			others.
		</blockquote>
		<p>
			A crawler visits each node, reads its nominations, and then visits those
			nodes in turn, recursively, building up a graph of all reachable nodes.
		</p>
		<p>
			The crawler runs periodically, so new nodes and nominations will appear on
			this page over time.
		</p>
	</details>

	<details class="qna" name="qna">
		<summary>questions</summary>
		<p>
			If you have inquiries (including wanting to join this webchain), you can
			come chat in the <a href="https://irc.milkmedicine.net" rel="external"
				>#webchain channel on irc.milkmedicine.net</a
			>.
		</p>
	</details>

	<details class="qna" name="qna">
		<summary>for members</summary>
		<p>
			If you want to link to this webchain from your site, an old-web style
			button is available:
		</p>
		<pre>
&lt;a href="{page.url.href}"&gt;
  &lt;img src="https://webchain.milkmedicine.net/button.png"&gt;
&lt;/a&gt;
		</pre>
		<p>
			<img src="button.png" class="button" alt="" />
		</p>
		<p>
			The <code>?node</code> query parameter can be used to highlight a specific
			node in the webchain (please use url-safe encoding).
		</p>
	</details>

	<ul class="nodes">
		<h2>members</h2>
		<p>
			{new Intl.NumberFormat("en-US").format(nodes.length)} sites in this webchain
		</p>
		{#each nodes as node, i (node.at)}
			<SidebarNode
				bind:this={node_components[node.at]}
				{node}
				index={i}
				{highlighted_node}
				{nominations_limit}
				{graph_component}
			/>
		{/each}
	</ul>
</aside>

<style>
	aside {
		position: absolute;
		top: 0;
		left: 0;
		padding: 0 1rem;
		background: linear-gradient(to right, white, transparent);
		min-height: 100vh;
		will-change: backdrop-filter;
	}

	.square {
		display: inline-block;
		width: 1.1em;
		height: 1.1em;
		background: blue;
		margin-right: 0.1em;
		vertical-align: sub;
	}

	aside > :last-child {
		margin-bottom: 20vh;
	}

	aside:hover {
		/* background: white; */
		border-right: 1px solid rgba(0, 0, 0, 0.25);
		background: linear-gradient(to right, white, rgba(255, 255, 255, 0.5));
		backdrop-filter: blur(1.5px);
	}

	summary {
		margin: 0;
	}

	details {
		max-width: 45ch;
	}

	details > :nth-child(2) {
		margin-top: 0;
	}

	.qna {
		padding: 0 0.5rem;
		border: 1px solid transparent;
	}

	.qna:has(> :focus-visible) {
		outline: 2px solid blue;
	}

	.qna summary:focus {
		outline: none;
	}

	.qna:is(:hover, :focus-visible) {
		border: 1px dashed currentColor;
	}

	.qna[open] {
		border: 1px dashed currentColor;
		background: #efefef;
		margin: 1rem 0;
	}

	.qna summary {
		padding: 0.5rem 0;
		font-style: italic;
	}

	.qna ol li {
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
</style>
