<script lang="ts">
	import type { DisplayNode } from "$lib/node"
	import { hovered_node, set_highlighted_node } from "$lib/node-state"
	import type Graph from "./Graph.svelte"
	import SidebarNode from "./SidebarNode.svelte"
	import { date_fmt, date_time_fmt } from "$lib/date"
	import { browser } from "$app/environment"
	import { onMount } from "svelte"

	let {
		at,
		nodes,
		highlighted_node,
		nominations_limit,
		graph_component,
		recent_nodes,
		render_children = true
	}: {
		at: string
		nodes: DisplayNode[]
		highlighted_node: string | undefined
		nominations_limit: number | null
		graph_component: Graph
		recent_nodes: string[]
		render_children?: boolean
	} = $props()

	let image_loaded = $state(!browser)
	let snap_image_element: HTMLImageElement | null = $state(null)

	const node = $derived.by(() => {
		const node = nodes.find((n) => n.at === at)
		if (!node) {
			throw new Error(`node with at="${at}" not found`)
		}
		return node
	})

	function hover_in() {
		hovered_node.set(node.at)
	}

	function hover_out() {
		if ($hovered_node === node.at) {
			hovered_node.set(undefined)
		}
	}

	onMount(() => {
		image_loaded = snap_image_element?.complete === true
	})
</script>

<li
	class:hovered={node.at === $hovered_node}
	class:highlighted={node.at === highlighted_node}
>
	<details open={node.at === highlighted_node} name="node">
		<summary
			class="node-header"
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
				if (["ArrowDown", "ArrowUp"].includes(event.key)) {
					const nodes = Array.from(
						document.querySelectorAll("#nodes summary")
					) as HTMLElement[]
					const index = nodes.findIndex((summary) => summary === event.target)
					if (index === -1) return

					const next_index = event.key === "ArrowDown" ? index + 1 : index - 1

					if (next_index >= 0 && next_index < nodes.length) {
						event.preventDefault()
						nodes.at(next_index)?.focus()
					}
				}
			}}
		>
			<div class="label" data-indexed={node.indexed}>
				<img
					src="/api/favicon?url={encodeURIComponent(node.at)}"
					alt="Favicon of {node.label}"
					width="16"
					height="16"
					style:background-color={node.generated_color}
				/>

				<span class="label-contents">
					{node.label}
					{#if recent_nodes.includes(at)}
						<span class="new" title="This node was recently added">new</span>
					{/if}
					{#if [$hovered_node, highlighted_node].includes(node.at)}
						<span
							class="slots"
							class:full={node.children.length === nominations_limit}
							title="This node has used {node.children
								.length}/{nominations_limit} of its nominations"
						>
							{node.indexed ? node.children.length : "?"}/{nominations_limit}
						</span>
					{/if}
				</span>
			</div>
		</summary>
		<div class="node-content">
			<a href={node.url.href} rel="external">
				<img
					src="/api/snap?url={encodeURIComponent(node.at)}"
					class="snap"
					data-loading={image_loaded ? undefined : "true"}
					alt="Screenshot of {node.label}"
					height="600"
					width="800"
					loading="lazy"
					bind:this={snap_image_element}
					onload={() => {
						image_loaded = true
					}}
					onerror={() => {
						image_loaded = true
					}}
				/>

				<h2>{node.html_metadata?.title || node.label}</h2>
			</a>

			{#if node.html_metadata?.description}
				<p>{node.html_metadata.description}</p>
			{/if}
			{#if !node.indexed}
				{#if node.index_error}
					<!-- <span class="small"><b>, the error is shown below</b></span> -->
					<div class="crawl-warning">
						<pre><code>{node.index_error}</code></pre>
					</div>
				{/if}
				<span class="small">
					this page was not crawled. is this your page?
					<a href="/doc/manual.md#my-page-is-not-being-crawled!"
						>see the manual</a
					></span
				>
			{/if}
			{#if node.first_seen}
				<p
					class="small date"
					title={date_time_fmt.format(node.first_seen).toLowerCase()}
				>
					first seen
					<time datetime={node.first_seen.toISOString()}>
						{date_fmt.format(node.first_seen).toLowerCase()}
					</time>
				</p>
			{/if}
		</div>
	</details>
</li>
{#if render_children === true && node.children.length > 0}
	<ul>
		{#each node.children as child_at}
			<SidebarNode
				at={child_at}
				{nodes}
				{highlighted_node}
				{nominations_limit}
				{graph_component}
				{recent_nodes}
			/>
		{/each}
	</ul>
{/if}

<style>
	li {
		display: flex;
		gap: 0.5ch;
		list-style-type: none;
		flex-direction: column;
		flex-grow: 1;
		max-width: 35ch;
	}

	li.hovered:not(.highlighted) {
		background-color: var(--color-shy);
	}

	details:has(summary:focus-visible) {
		border-left: 2px solid var(--color-primary);
	}

	li:has(details[open]) + ul {
		border-image: repeating-linear-gradient(
				to bottom,
				var(--color-border),
				var(--color-border) 4px,
				transparent 4px,
				transparent 8px
			)
			1;
	}

	li:is(.hovered, :hover) + ul {
		border-color: var(--color-shy);
	}

	ul {
		border-left: 2px solid var(--color-solid);
		padding-left: 0.5ch;
	}

	.label {
		display: flex;
		flex: 1;
		align-items: center;
		gap: 0.5ch;
		padding: 0.15em 0.15em 0.15em 0.2em;
		line-height: 1;
	}

	.label-contents {
		display: flex;
		align-items: center;
		gap: 0 0.5ch;
	}

	.label .new {
		background-color: var(--color-primary);
		color: var(--color-text-primary);
		border: 1px solid currentColor;
		font-family: "Fantasque Sans Mono", monospace;
		border-radius: 0.3rem;
		padding: 0.075rem 0.15rem;
		line-height: 1;
		font-size: 0.75rem;
		align-self: center;
		box-sizing: border-box;
		user-select: none;
		text-wrap: nowrap;
	}

	.label .slots {
		font-size: 0.75em;
		font-family: "Fantasque Sans Mono", monospace;
		vertical-align: middle;
		user-select: none;
	}

	li details[open] .label {
		background-color: var(--color-primary);
		color: white;
	}

	.label img {
		display: block;
		border-radius: 0.1rem;
		border: 1px solid var(--color-shy);
		aspect-ratio: 1 / 1;
		color: transparent; /* hide alt text */
	}

	/* Only apply opacity when details is NOT open and node is not indexed */
	li details:not([open]) .label[data-indexed="false"] > * {
		opacity: 0.5;
	}

	.node-header {
		all: unset;
		color: var(--color-text);
		display: flex;
		gap: 0.25em;
		word-break: break-all;
	}

	.node-content {
		border-left: 2px solid var(--color-primary);
		padding: 0.4rem;
		display: flex;
		flex: 1;
		flex-direction: column;
		/* max-width: 35ch; */
		background: var(--color-solid);
	}

	.node-content h2 {
		all: unset;
		display: block;
		margin-top: 0.4rem;
	}

	.node-content p {
		margin: 0;
		margin-top: 0.4rem;
		overflow: hidden;
		text-overflow: ellipsis;
	}

	.node-content a {
		font-weight: bold;
		word-break: break-word;
	}

	.node-content a:hover {
		text-decoration-style: double;
	}

	.small {
		font-size: 0.85em;
		opacity: 0.8;
		margin: 0.2rem 0;
	}

	.date {
		font-style: italic;
	}

	.crawl-warning {
		display: flex;
		flex-grow: 0;
		margin: 0;
		font-family: "Fantasque Sans Mono", monospace;
		font-size: 0.8rem;
		padding: 0.25rem;
		border: 1px solid var(--color-border);
		margin-top: 0.4rem;
	}

	.crawl-warning pre {
		margin: 0;
		text-wrap: wrap;
	}

	.snap {
		display: block;
		max-width: 80%;
		height: auto;
		font-weight: normal;
		font-size: 0.9rem;
		font-family: "Fantasque Sans Mono", monospace;
		text-decoration: none;
		color: var(--color-border);
		background: var(--color-bg);
	}

	@keyframes loading {
		0% {
			opacity: 0.5;
		}
		100% {
			opacity: 1;
		}
	}

	.snap[data-loading="true"] {
		animation: loading 400ms infinite alternate;
	}
</style>
