<script lang="ts">
	import { onMount } from "svelte"
	import type { PageProps } from "./$types"
	import Graph from "./Graph.svelte"
	import Sidebar from "./Sidebar.svelte"
	import { goto } from "$app/navigation"
	import { page } from "$app/state"

	let { data }: PageProps = $props()
	let graph_component: Graph | undefined = $state()

	onMount(async () => {
		const url_param = page.url.searchParams.get("node")
		const current_node = data.nodes.find(
			(n) => n.url_param === url_param || n.at === url_param
		)

		if (!current_node) return

		const new_url = new URL(page.url)
		new_url.searchParams.set("node", current_node.url_param)

		await goto("?" + new_url.searchParams.toString(), {
			state: {
				node: current_node.at
			},
			replaceState: true,
			noScroll: true
		})
	})
</script>

<svelte:head>
	<!-- common webchain metadata -->
	<link rel="webchain" href="https://webchain.milkmedicine.net" />
	<link rel="webchain-nomination" href="https://irc.milkmedicine.net/" />
	<link rel="webchain-nomination" href="https://www.himawari.fun/" />
	<link rel="webchain-nomination" href="https://nekopath.fun/" />
	<link rel="webchain-nomination" href="https://eidoli.ca" />

	<!-- set the nominations limit for each node - root only -->
	<meta name="webchain-nominations-limit" content="4" />

	<title>milkmedicine webchain</title>
	<meta
		name="description"
		content="a distributed webring for friends and enemies. you are here!"
	/>
	<meta name="theme-color" content="#0000ff" />
</svelte:head>

<div class="container">
	<Graph nodes={data.nodes} bind:this={graph_component}></Graph>
	<Sidebar
		nodes={data.nodes}
		{graph_component}
		nominations_limit={data.nominations_limit}
		crawl_date={data.end}
	></Sidebar>
</div>

<style>
	.container {
		position: relative;
	}
</style>
