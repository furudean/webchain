<script lang="ts">
	import type { Node } from "$lib/node"
	let {
		nodes,
		highlighted_node = $bindable(),
		hovered_node = $bindable()
	}: {
		nodes: Node[]
		highlighted_node?: string
		hovered_node?: string
	} = $props()
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
				class:highlighted={node.at === highlighted_node}
				class:hovered={node.at === hovered_node}
			>
				<a
					href={node.at}
					style:margin-left="{node.depth}ch"
					target="_blank"
					onmouseenter={(e) => {
						hovered_node = node.at
					}}
					onmouseleave={(e) => {
						hovered_node = undefined
					}}
					>{node.url.host}</a
				>
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
		border: 1px dashed grey;
		background: rgba(255, 255, 255, 0.8);
		backdrop-filter: blur(4px);
		padding: 0.5rem;
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
		margin: 0.5rem 0;
	}

	.nodes li.highlighted {
		background-color: blue;
		color: white;
	}

	.nodes li.hovered:not(.highlighted),
	.nodes li:hover:not(.highlighted) {
		background-color: #8e8e8e36;
	}

	.nodes a {
		color: currentColor;
		flex: 1
	}
</style>
