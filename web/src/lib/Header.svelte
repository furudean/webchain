<script lang="ts">
	import { page } from "$app/state"

	const routes = [
		["/", "graph"],
		["/gallery", "gallery"],
		["/doc", "docs"]
	]
</script>

<header aria-labelledby="title">
	<span id="title">
		<span class="square" aria-hidden="true"></span> the milkmedicine webchain
	</span>
	<nav>
		<ul>
			{#each routes as [href, label]}
				<li>
					<a
						{href}
						aria-current={href === page.url.pathname ? "page" : undefined}
						>{label}</a
					>
				</li>
			{/each}
		</ul>
	</nav>
</header>

<style>
	.square {
		display: inline-block;
		width: 1.1em;
		height: 1.1em;
		background: var(--color-primary);
		margin-right: 0.1em;
		vertical-align: sub;
	}

	header {
		display: flex;
		flex-wrap: wrap;
		align-items: center;
		margin: 2rem 1rem;
		gap: 2rem;
	}

	#title {
		font-size: 1.25rem;
		margin-bottom: 0;
		font-weight: bold;
	}

	nav {
		display: inline;
	}

	ul {
		display: inline-flex;
		gap: 1rem;
		padding: 0;
		margin: 0;
		list-style: none;
	}

	li {
		margin: 0;
	}

	:any-link {
		color: var(--a-not-visited-color);
		font-weight: 500;
	}

	:any-link::before {
		content: "/";
	}

	a[aria-current="page"] {
		text-decoration: underline;
	}
</style>
