<script lang="ts">
	import type { PageProps } from "./$types"

	let { data }: PageProps = $props()
</script>

<svelte:head>
	<title>docs · milkmedicine webchain</title>
</svelte:head>

<h1>Docs index</h1>
<ul>
	{#each data.routes as route}
		<li>
			<a href="/doc/{route.slug}">{route.slug}</a>
		</li>
	{/each}
</ul>
