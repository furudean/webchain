<script lang="ts">
	import "../app.css"
	import { goto } from "$app/navigation"
	import { page } from "$app/state"
	import { onMount } from "svelte"

	let { children } = $props()

	onMount(() => {
		goto("", {
			state: {
				node: page.url.searchParams.get("node") || undefined
			}
		})
	})
</script>

{@render children?.()}
