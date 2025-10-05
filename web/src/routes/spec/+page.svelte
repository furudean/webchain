<script lang="ts">
	import type { PageProps } from "./$types"

	let { data }: PageProps = $props()
</script>

<main>
	{@html data.html}
</main>

<style>
	main {
		max-width: 32rem;
		padding: 0 1rem;
	}
</style>
