<script lang="ts">
	import type { Node } from "$lib/node"
	import { hovered_node, graph, set_highlighted_node } from "$lib/node_state"
	import { page } from "$app/state"
	import Graph from "./Graph.svelte"

	let {
		nodes,
		nominations_limit,
		graph_component
	}: {
		nodes: Node[]
		nominations_limit: number | null
		graph_component: Graph
	} = $props()

	const highlighted_node = $derived(page.state.node)

	let node_elements: Record<string, HTMLElement> = $state({})

	$effect(() => {
		if (highlighted_node === undefined) return
		const current_element = node_elements[highlighted_node]
		if (!current_element) return
		current_element.scrollIntoView({ behavior: "auto", block: "center" })
	})

	function hover_in(at: string | undefined) {
		if ($graph?.hasNode(at)) {
			$graph.setNodeAttribute(at, "highlighted", true)
		}
		hovered_node.set(at)
	}

	function hover_out(at: string | undefined) {
		if ($graph?.hasNode(at) && at !== highlighted_node) {
			$graph.setNodeAttribute(at, "highlighted", false)
		}
		hovered_node.set(undefined)
	}
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
			A <a
				href="https://github.com/furudean/webchain/blob/main/SPEC.md"
				rel="external">webchain</a
			>
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

	<ul class="nodes">
		<h2>members</h2>
		<p>
			{new Intl.NumberFormat("en-US").format(nodes.length)} sites in this webchain
		</p>
		{#each nodes as node, i (node.at)}
			<li
				class:highlighted={node.at === highlighted_node}
				class:hovered={node.at === $hovered_node}
				style:margin-left="{node.depth}ch"
				aria-describedby="{node.hash}-desc"
			>
				<details
					open={node.at === highlighted_node}
					name="nodes"
					bind:this={node_elements[node.at]}
				>
					<summary
						class="node-header"
						id="{node.hash}-desc"
						onmouseenter={() => hover_in(node.at)}
						onmouseleave={() => hover_out(node.at)}
						onfocusin={() => hover_in(node.at)}
						onfocusout={() => hover_out(node.at)}
						onclick={(e) => {
							e.preventDefault()
							if (node.at === highlighted_node) {
								set_highlighted_node(undefined)
							} else {
								set_highlighted_node(node.at)
							}
							graph_component.center_on_nodes([node.at])
						}}
						onkeydown={(event) => {
							if (event.key === "ArrowDown") {
								event.preventDefault()
								const next = document.querySelectorAll(".nodes summary")[i + 1]
								if (next) (next as HTMLElement).focus()
							}
							if (event.key === "ArrowUp") {
								event.preventDefault()
								const prev = document.querySelectorAll(".nodes summary")[i - 1]
								if (prev) (prev as HTMLElement).focus()
							}
						}}
					>
						<div class="label" data-indexed={node.indexed}>
							<img
								src="/api/favicon?url={encodeURIComponent(node.at)}"
								alt=""
								aria-hidden="true"
								width="16"
								height="16"
								style:background-color={node.generated_color}
							/>
							<span>
								{node.label}
								{#if [$hovered_node, highlighted_node].includes(node.at)}
									<span
										class="slots"
										class:full={node.children.length === nominations_limit}
									>
										{#if node.indexed}
											{node.children.length}/{nominations_limit}
										{:else}
											offline
										{/if}
									</span>
								{/if}
							</span>
						</div>
					</summary>
					{#if highlighted_node === node.at}
						<div class="node-content">
							<a href={node.url.href} rel="external">
								{node.html_metadata?.title || node.label}
							</a>
							{#if node.html_metadata?.description}
								<p>{node.html_metadata.description}</p>
							{/if}
						</div>
					{/if}
				</details>
			</li>
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

	.qna blockquote {
		margin: 0;
		padding-left: 0.5rem;
		border-left: 2px solid currentColor;
		font-style: italic;
		color: #555;
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

	.nodes li {
		display: flex;
		gap: 0.5ch;
		list-style-type: none;
		display: flex;
		flex-direction: column;
		flex: 1;
	}

	.nodes li:is(.hovered, :hover):not(.highlighted) {
		background-color: #8e8e8e36;
	}

	.nodes li:has(summary:focus-visible) {
		border-left: 2px solid blue;
	}

	.label {
		display: flex;
		flex: 1;
		align-items: center;
		gap: 0.5ch;
		padding: 0 0.4em;
	}

	.label .slots {
		font-size: 0.75em;
		font-family: monospace;
		vertical-align: middle;
		color: currentColor;
		user-select: none;
		pointer-events: none;
		margin-left: 0.5ch;
	}

	.nodes li details[open] .label {
		background-color: blue;
		color: white;
	}

	.label img {
		display: block;
		border-radius: 0.1rem;
	}

	.label[data-indexed="false"] > * {
		opacity: 0.65;
	}

	.node-header {
		all: unset;
		color: currentColor;
		line-height: 1.5;
		display: flex;
		gap: 0.25em;
	}

	.node-content {
		border-left: 2px solid blue;
		padding: 0.4rem;
		display: flex;
		flex: 1;
		flex-direction: column;
	}

	.node-content p {
		margin: 0;
		margin-top: 0.4rem;
		max-width: 35ch;
		overflow: hidden;
		text-overflow: ellipsis;
		font-style: italic;
	}

	.node-content a {
		color: blue;
		font-weight: bold;
	}

	.node-content a:hover {
		text-decoration-style: double;
	}

	.node-content a:visited {
		color: purple;
	}
</style>
