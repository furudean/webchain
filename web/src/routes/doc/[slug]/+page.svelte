<script lang="ts">
	import type { PageProps } from "./$types"

	let { data }: PageProps = $props()
</script>

<svelte:head>
	{#if data.frontmatter?.title}
		<title>{data.frontmatter.title}</title>
	{/if}
</svelte:head>

<main>
	{@html data.html}
</main>

<style>
	main {
		max-width: 32rem;
		padding: 0 1rem;
	}
</style>
