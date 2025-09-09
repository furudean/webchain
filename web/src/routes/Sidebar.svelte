<script lang="ts">
	import type { Node } from "$lib/node"
	import {
		highlighted_node,
		hovered_node,
		current_graph,
		set_highlighted_node,
		set_hovered_node,
		clear_highlighted
	} from "$lib/node_state"
	import { get } from "svelte/store"

	let { nodes }: { nodes: Node[] } = $props()
</script>

<aside>
	<h1>the<br />milkmedicine<br />webchain</h1>

	<p>a distributed webring for friends and enemies</p>

	<details class="qna">
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
		<p>
			Source code can be found <a
				href="https://github.com/furudean/webchain"
				rel="external">on our GitHub</a
			>.
		</p>
	</details>

	<details class="qna">
		<summary>how?</summary>
		<p>Each member node adds markup to their HTML, for example:</p>
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
&lt;body&gt;...&lt/body&gt;
&lt/html&gt;</code
			></pre>
		<p>
			The <code>webchain</code> link points to the node's own URL, while the
			<code>webchain-nomination</code> links point to up to three other websites
			that this node nominates.
		</p>
		<p>
			A crawler visits each node, reads its nominations, and then visits those
			nodes in turn, recursively, building up a graph of all reachable nodes.
		</p>
		<p>
			The crawler runs periodically, so new nodes and nominations will appear on
			this page over time.
		</p>
	</details>

	<hr />

	<ul class="nodes">
		{#each nodes as node}
			<li
				class:highlighted={node.at === $highlighted_node}
				class:hovered={node.at === $hovered_node}
				style:margin-left="{node.depth}ch"
			>
				<details open={$highlighted_node === node.at}>
					<summary
						class="node-header"
						onclick={(event) => {
							event.preventDefault()
							const graph = get(current_graph)
							clear_highlighted(graph)
							set_highlighted_node(node.at)
							$highlighted_node = node.at
						}}
						onmouseenter={() => {
							set_hovered_node(node.at)
							const graph = get(current_graph)
							if (graph && graph.hasNode(node.at)) {
								graph.setNodeAttribute(node.at, "highlighted", true)
							}
						}}
						onmouseleave={() => {
							set_hovered_node(undefined)
							const graph = get(current_graph)
							if (
								graph &&
								graph.hasNode(node.at) &&
								node.at !== $highlighted_node
							) {
								graph.setNodeAttribute(node.at, "highlighted", false)
							}
						}}
					>
						<div class="label">
							<img
								src="/api/favicon?url={encodeURIComponent(node.at)}"
								alt=""
								aria-hidden="true"
								width="16"
								height="16"
								style:background-color={node.color}
							/>
							<span>{node.label}</span>
							{#if node.depth === 0}
								<em style="margin-top: 0.14em;">(you are here!)</em>
							{/if}
						</div>
					</summary>
					{#if $highlighted_node === node.at}
						<div class="node-content">
							<a href={node.url.href} rel="external">
								{node.html_metadata?.title || node.label}
							</a>
							{#if node.html_metadata?.description}
								<p>{node.html_metadata.description}</p>
							{:else}
								<p class="shy">
									<em>no description</em>
								</p>
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

	.qna[open] {
		border: 1px dashed currentColor;
		background: rgba(255, 255, 255, 0.9);
		margin-bottom: 1rem;
	}

	summary {
		cursor: pointer;
		padding: 0.5rem 0;
	}

	.qna ol li {
		margin: 0.5rem 0;
	}

	ul {
		margin: 0;
		padding: 0;
	}

	hr {
		margin: 1rem 0;
		border: none;
		border-top: 1px dashed currentColor;
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

	.nodes li.hovered:not(.highlighted) {
		background-color: #8e8e8e36;
	}

	.label {
		display: flex;
		flex: 1;
		align-items: center;
		gap: 0.5ch;
		padding: 0 0.4em;
	}

	.nodes li details[open] .label {
		background-color: blue;
		color: white;
	}

	.label img {
		display: block;
		border-radius: 0.1rem;
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
		background: linear-gradient(
			to bottom,
			rgba(255, 255, 255, 0.5),
			transparent
		);
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

	.node-content a:visited {
		color: purple;
	}

	.shy {
		opacity: 0.75;
	}
</style>
