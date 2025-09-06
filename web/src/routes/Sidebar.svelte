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
	<h1>the<br>milkmedicine<br>webchain</h1>

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
				<div class="node-container" role="listitem">
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
						<div class="label">
							{node.label}
							{#if node.depth === 0}
								<em style="margin-top: 0.14em;">(you are here!)</em>
							{/if}
						</div>
						<!-- <span>{expandedNodes[node.at] ? "▼" : "▶"}</span> -->
					</button>
					{#if $highlighted_node === node.at}
						<div class="node-content">
							<a href={node.url.href}
								>{node.html_metadata?.title || node.label}</a
							>
							{#if node.html_metadata?.description}
								<p>{node.html_metadata.description}</p>
							{/if}
						</div>
					{/if}
				</div>
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

	.nodes li.hovered:not(.highlighted) {
		background-color: #8e8e8e36;
	}

	.nodes li.highlighted .label {
		background-color: blue;
		color: white;
		flex: 1;
	}

	.node-container {
		display: flex;
		flex-direction: column;
		flex: 1;
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
		background: linear-gradient(to bottom, white, transparent);
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
</style>
