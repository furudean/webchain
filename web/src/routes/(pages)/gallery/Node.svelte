<script lang="ts">
	import type { DisplayNode } from "$lib/node"
	import { date_fmt } from "$lib/date"
	import { browser } from "$app/environment"
	import { onMount } from "svelte"

	let {
		node,
		parent_node,
		children
	}: {
		node: DisplayNode
		parent_node: DisplayNode | undefined
		children: DisplayNode[]
	} = $props()

	let snap_load_finished = $state(!browser)
	let snap_image_element: HTMLImageElement | null = $state(null)

	onMount(() => {
		snap_load_finished = snap_image_element?.complete === true
	})
</script>

<li id="node-{node.url_param}">
	<a href={node.url.href} rel="external">
		{#if node.robots_ok}
			<img
				src="/api/snap?url={encodeURIComponent(node.at)}"
				class="snap"
				data-loading={snap_load_finished ? undefined : "true"}
				alt="screenshot of {node.label}"
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
		{:else}
			<div class="snap">photo not allowed by robots.txt</div>
		{/if}

		<div class="title">
			<img
				src="/api/favicon?url={encodeURIComponent(node.at)}"
				alt="Favicon for {node.label}"
				aria-hidden="true"
				class="favicon"
				width="16"
				height="16"
				style:background-color={node.generated_color}
			/>
			<span class="label">
				{node.html_metadata?.title || node.label}
				{#if node.is_recent}
					<span class="new" title="This node was recently added">new</span>
				{/if}
			</span>
			{#if node.label !== node.html_metadata?.title}
				<span class="url">{node.label}</span>
			{/if}
		</div>
	</a>

	{#if node.html_metadata?.description}
		<p>{node.html_metadata.description}</p>
	{/if}

	{#if children.length > 0}
		<p class="nominates">
			<span class="site-label">{node.label}</span> nominates {children.length >
			0
				? children.length
				: "no"} site{children.length === 1 ? "" : "s"}
		</p>
		<ol class="nominates">
			{#each children as child}
				<li>
					<a
						href="#node-{child.url_param}"
						data-sveltekit-replacestate
						class="site-label">{child.label}</a
					>
				</li>
			{/each}
		</ol>
	{/if}

	<p class="small">
		{#if parent_node}
			nominated by <a
				href="#node-{parent_node.url_param}"
				data-sveltekit-replacestate
				class="site-label">{parent_node.label}</a
			>
		{/if}
		{#if parent_node && node.first_seen}
			<span class="sep">·</span>
		{/if}
		{#if node.first_seen}
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
		border-radius: 0.1rem;
		border: 1px solid var(--color-shy);
		aspect-ratio: 1 / 1;
		color: transparent; /* hide alt text */
		image-rendering: pixelated;
	}

	.title {
		display: grid;
		grid-template-columns: auto minmax(0, 1fr);
		grid-template-areas:
			"a b"
			"a c";
		column-gap: 0.4em;
	}

	.title > img {
		grid-area: a;
	}

	.title > .label {
		grid-area: b;
		line-height: 1;
	}

	.title > .url {
		grid-area: c;
		font-family: "Fantasque Sans Mono", monospace;
		font-size: 0.85em;
		font-weight: normal;
		color: var(--color-text);
		opacity: 0.75;
		text-decoration: none;
		margin-top: 3px;
	}

	p {
		margin: 0.6rem 0;
	}

	.nominates {
		font-size: 0.85em;
	}

	p.nominates {
		margin-bottom: 0;
	}

	ol.nominates {
		margin-top: 0;
		padding-left: 0;
		margin-left: 2.5em;
		display: grid;
		grid-template-columns: repeat(auto-fit, minmax(10rem, 1fr));
		column-gap: 2em;
	}

	a {
		word-break: break-all;
	}

	a span {
		text-decoration: underline;
	}

	a:hover span {
		text-decoration-style: double;
	}

	a[rel="external"] {
		font-weight: bold;
		word-break: break-word;
		text-decoration: none;
	}

	a[href^="#"] {
		color: inherit;
	}

	.small {
		font-size: 0.85em;
		opacity: 0.75;
	}

	.snap {
		display: block;
		max-width: 100%;
		height: auto;
		font-family: "Fantasque Sans Mono", monospace;
		font-variant-ligatures: none;
		font-weight: normal;
		font-size: 0.9rem;
		text-decoration: none;
		border: 1px solid var(--color-border);
		color: var(--color-shy);
		margin-bottom: 0.4rem;
		aspect-ratio: 4 / 3;
		display: flex;
		justify-content: center;
		align-items: center;
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

	.new {
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
		text-decoration: none;
	}

	.site-label {
		font-family: "Fantasque Sans Mono", monospace;
		font-variant-ligatures: none;
	}
</style>
