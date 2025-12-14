<script lang="ts">
	import type { PageProps } from "./$types"

	let { data }: PageProps = $props()
</script>

<svelte:head>
	<title>documentation · milkmedicine webchain</title>
</svelte:head>

<h1>documents index</h1>
<p>
	Some pages that may help you if you want to understand the webchain concept,
	or how it works.
</p>
<ul>
	{#each data.routes as route}
		<li>
			<a href="/doc/{route.slug}">{route.slug}</a>
		</li>
	{/each}
</ul>
