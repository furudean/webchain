<script lang="ts">
	let {
		start,
		end
	}: {
		start: string | null | undefined
		end: string | null | undefined
	} = $props()
</script>

<aside>
	<h1>milkmedicine webchain</h1>
	<p>
		a <a
			href="https://github.com/furudean/webchain/blob/main/SPEC.md"
			rel="external">webchain</a
		>
		is a distributed
		<a href="https://en.wikipedia.org/wiki/Webring" rel="external">webring</a>,
		where each member can nominate other websites, creating a walkable graph of
		trust.
	</p>
	<p>
		The current state of the <em>milkmedicine webchain</em> is visualized on this
		page.
	</p>
	<p>It's still in development... so please be nice.</p>
	<ol>
		<li>
			This page is the starting point of the <em>milkmedicine webchain</em>,
			which nominates three other websites
		</li>
		<li>
			Nominated websites may add their own nominations by adding markup to their
			HTML, up to a limit of three.
		</li>
		<li>Those websites may nominate three others, and so on, and so forth.</li>
	</ol>
	{#if start && end}
		The last crawl fininished {new Date(end).toLocaleString("en-US").toLowerCase()},
		which took {(new Date(end).getTime() - new Date(start).getTime()) / 1000} seconds
	{/if}
</aside>

<style>
	aside {
		grid-area: aside;
		position: relative;
		z-index: 1;
		padding: 0 1rem;
	}
</style>
