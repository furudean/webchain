<script lang="ts">
	import type { DisplayNode } from "$lib/node"
	import { date_fmt } from "$lib/date"
	import { browser } from "$app/environment"
	import { onMount } from "svelte"
	import { version } from "$app/environment"

	let {
		node,
		parent_node,
		recent_nodes
	}: {
		node: DisplayNode
		parent_node: DisplayNode | undefined
		recent_nodes: string[]
	} = $props()

	let snap_load_finished = $state(!browser)
	let snap_image_element: HTMLImageElement | null = $state(null)

	onMount(() => {
		snap_load_finished = snap_image_element?.complete === true
	})
</script>

<li id="node-{node.url_param}">
	<a href={node.url.href} rel="external">
		<img
			src="/api/snap?url={encodeURIComponent(node.at)}&version={version}"
			class="snap"
			data-loading={snap_load_finished ? undefined : "true"}
			alt="Screenshot of {node.label}"
			height="768"
			width="1024"
			loading="lazy"
			bind:this={snap_image_element}
			onload={() => {
				snap_load_finished = true
			}}
			onerror={() => {
				snap_load_finished = true
			}}
		/>
		<img
			src="/api/favicon?url={encodeURIComponent(node.at)}"
			alt="Favicon for {node.label}"
			aria-hidden="true"
			class="favicon"
			width="16"
			height="16"
			style:background-color={node.generated_color}
		/>
		<span>{node.html_metadata?.title || node.label}</span>
	</a>

	{#if node.html_metadata?.description}
		<p>{node.html_metadata.description}</p>
	{/if}

	{#if !node.indexed}
		<div class="crawl-warning">
			this page was not crawled. is this your page?
			<a href="/doc/manual.md#my-page-is-not-being-crawled!">see the manual</a>
		</div>
	{/if}
	<p class="small">
		{#if parent_node}
			nominated by <a
				href="#node-{parent_node.url_param}"
				data-sveltekit-replacestate>{parent_node.label}</a
			>
		{/if}
		{#if parent_node && node.first_seen}
			<span class="sep">·</span>
		{/if}
		{#if node.first_seen}
			first seen
			<time datetime={node.first_seen.toISOString()}>
				{date_fmt.format(node.first_seen).toLowerCase()}
			</time>
		{/if}
	</p>
</li>

<style>
	li:target {
		outline: 3px solid var(--color-primary);
		outline-offset: 3px;
	}

	.favicon {
		display: inline-block;
		vertical-align: middle;
		border-radius: 0.1rem;
		border: 1px solid var(--color-shy);
		aspect-ratio: 1 / 1;
		color: transparent; /* hide alt text */
	}

	p {
		margin: 0.4rem 0;
	}

	a[rel="external"] {
		font-weight: bold;
		word-break: break-word;
		text-decoration: none;
	}

	a span {
		text-decoration: underline;
	}

	a:hover span {
		text-decoration-style: double;
	}

	a[href^="#"] {
		color: inherit;
		font-weight: inherit;
		text-decoration: underline;
	}

	.small {
		font-size: 0.85em;
		opacity: 0.8;
		font-style: italic;
	}

	.crawl-warning {
		border: 1px solid var(--color-border);
		font-size: 0.85em;
		padding: 0.25em;
		margin: 0.4rem 0;
	}

	.snap {
		display: block;
		box-sizing: border-box;
		max-width: 100%;
		height: auto;
		font-weight: normal;
		font-size: 0.9rem;
		font-family: "Fantasque Sans Mono", monospace;
		text-decoration: none;
		border: 1px solid var(--color-border);
		color: var(--color-text);
		margin-bottom: 0.4rem;
	}

	@keyframes loading {
		0% {
			opacity: 1;
		}
		100% {
			opacity: 0.5;
		}
	}

	.snap[data-loading="true"] {
		animation: loading 300ms infinite alternate;
	}

	.sep {
		user-select: none;
	}
</style>
