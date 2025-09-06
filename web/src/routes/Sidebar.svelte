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
	<h1>milkmedicine webchain</h1>

	<details class="what">
		<summary>what?</summary>
		<p>
			a <a
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
	</details>

	<ul class="nodes">
		{#each nodes as node}
			<li
				class:highlighted={node.at === $highlighted_node}
				class:hovered={node.at === $hovered_node}
				style:margin-left="{node.depth}ch"
			>
				<div role="listitem">
					<button
						class="node-header"
						type="button"
						aria-expanded={$highlighted_node === node.at}
						onclick={() => {
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
						<div class="label">{node.label}</div>
						<!-- <span>{expandedNodes[node.at] ? "▼" : "▶"}</span> -->
					</button>
					{#if $highlighted_node === node.at}
						<a href={node.url.href}>{node.url.href}</a>
					{/if}
				</div>
				{#if node.depth === 0}
					<em>(you are here!)</em>
				{/if}
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
	}

	summary {
		margin: 0;
	}

	details {
		max-width: 45ch;
	}

	.what {
		border: 1px dashed currentColor;
		background: rgba(255, 255, 255, 0.9);
		/* backdrop-filter: blur(4px); */
		padding: 0 0.5rem;
	}

	summary {
		cursor: pointer;
		padding: 0.5rem 0;
	}

	.what ol li {
		margin: 0.5rem 0;
	}

	ul {
		margin: 0;
		padding: 0;
	}

	.nodes {
		float: left;
		margin-top: 1rem;
	}

	.nodes li {
		display: flex;
		gap: 0.5ch;
		list-style-type: none;
	}



	.nodes li.hovered:not(.highlighted),
	.nodes li:hover:not(.highlighted) {
		background-color: #8e8e8e36;
	}

	.nodes li.highlighted .label {
		background-color: blue;
		color: white;
	}

	button {
		all: unset;
		color: currentColor;
		line-height: 1.5;
	}

	.node-header {
		display: flex;
		gap: 0.25em;
	}
</style>
