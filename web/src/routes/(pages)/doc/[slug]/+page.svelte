<script lang="ts">
	import type { PageProps } from "./$types"

	let { data }: PageProps = $props()
</script>

<svelte:head>
	{#if data.frontmatter?.title}
		<title>{data.frontmatter.title}</title>
	{/if}
</svelte:head>

<article>
	{@html data.html}
</article>
