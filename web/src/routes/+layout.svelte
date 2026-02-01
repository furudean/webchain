<script lang="ts">
	import { page } from "$app/state"
	import "../app.css"

	const snap_qs = $derived.by(() => {
		const qs = new URLSearchParams()
		qs.set("path", page.url.pathname)
		return qs
	})

	const snap_url = $derived(
		new URL("/api/snap?" + snap_qs, page.url.protocol + page.url.host)
	)

	let { children } = $props()
</script>

<svelte:head>
	<link rel="shortcut icon" href="/favicon.png" type="image/png" />
	<meta name="theme-color" content="#0000ff" />

	<!-- provide a preview image of the current page -->

	<meta name="twitter:card" content="summary_large_image" />
	<meta name="twitter:image" content={snap_url.href} />

	<meta property="og:type" content="website" />
	<meta property="og:image" content={snap_url.href} />
	<meta property="og:image:width" content="1024" />
	<meta property="og:image:height" content="768" />
	<meta property="og:image:type" content="image/webp" />

	<link
		rel="alternate"
		type="application/rss+xml"
		href="/rss.xml"
		title="milkmedicine rss feed"
	/>

	<link
		rel="alternate"
		type="text/xml+opml"
		href="/feeds.opml"
		title="milkmedicine webchain member feeds"
	/>
</svelte:head>

{@render children?.()}
