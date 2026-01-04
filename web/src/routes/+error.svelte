<script lang="ts">
	import { page } from "$app/state"
	import Header from "$lib/Header.svelte"
</script>

<Header></Header>

<main>
	<article>
		<h1>{page.status} {page.error?.message}</h1>
	</article>
</main>
