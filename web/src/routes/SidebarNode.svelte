<script lang="ts">
	import type { DisplayNode } from "$lib/node"
	import { hovered_node, graph, set_highlighted_node } from "$lib/node-state"
	import type Graph from "./Graph.svelte"

	let {
		node,
		index,
		highlighted_node,
		nominations_limit,
		graph_component
	}: {
		node: DisplayNode
		index: number
		highlighted_node: string | undefined
		nominations_limit: number | null
		graph_component: Graph
	} = $props()

	let node_element: HTMLElement | undefined = $state()

	function hover_in() {
		if ($graph?.hasNode(node.at)) {
			$graph.setNodeAttribute(node.at, "highlighted", true)
		}
		hovered_node.set(node.at)
	}

	function hover_out() {
		if ($graph?.hasNode(node.at) && node.at !== highlighted_node) {
			$graph.setNodeAttribute(node.at, "highlighted", false)
		}
		hovered_node.set(undefined)
	}

	export function scrollIntoView() {
		if (node_element) {
			node_element.scrollIntoView({ behavior: "auto", block: "center" })
		}
	}
</script>

<li
	class:highlighted={node.at === highlighted_node}
	class:hovered={node.at === $hovered_node}
	style:margin-left="{node.depth}ch"
	aria-describedby="{node.hash}-desc"
>
	<details
		open={node.at === highlighted_node}
		name="nodes"
		bind:this={node_element}
	>
		<summary
			class="node-header"
			id="{node.hash}-desc"
			onmouseenter={hover_in}
			onmouseleave={hover_out}
			onfocusin={hover_in}
			onfocusout={hover_out}
			onclick={(e) => {
				e.preventDefault()
				if (node.at === highlighted_node) {
					set_highlighted_node(undefined)
				} else {
					set_highlighted_node(node.at, node.url_param)
				}
				graph_component.center_on_nodes([node.at])
			}}
			onkeydown={(event) => {
				if (event.key === "ArrowDown") {
					event.preventDefault()
					const next = document.querySelectorAll(".nodes summary")[index + 1]
					if (next) (next as HTMLElement).focus()
				}
				if (event.key === "ArrowUp") {
					event.preventDefault()
					const prev = document.querySelectorAll(".nodes summary")[index - 1]
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
		<div class="node-content">
			<a href={node.url.href} rel="external">
				{node.html_metadata?.title || node.label}
			</a>
			{#if node.html_metadata?.description}
				<p>{node.html_metadata.description}</p>
			{/if}
		</div>
	</details>
</li>

<style>
	li {
		display: flex;
		gap: 0.5ch;
		list-style-type: none;
		display: flex;
		flex-direction: column;
		flex: 1;
	}

	li:is(.hovered, :hover):not(.highlighted) {
		background-color: #8e8e8e36;
	}

	li:has(summary:focus-visible) {
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

	li details[open] .label {
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
