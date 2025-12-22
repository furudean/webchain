<script lang="ts">
	import { browser } from "$app/environment"
	import { goto, replaceState } from "$app/navigation"
	import { page } from "$app/state"
	import type { DisplayNode } from "./node"

	export interface Sort {
		key: string
		value: string
		fn: (a: DisplayNode, b: DisplayNode) => number
	}

	let {
		sort_value = $bindable(),
		sorts
	}: {
		sort_value: string | undefined | null
		sorts: Sort[]
	} = $props()

	function url_with_sort(type: string | undefined | null): string {
		const params = new URLSearchParams(page.url.searchParams)

		if (!type || type === sorts[0].key) {
			params.delete("sort")
		} else {
			params.set("sort", type)
		}

		return params.size ? "?" + params.toString() : ""
	}

	const url = $derived(page.url)

	$effect(() => {
		const param = url.searchParams.get("sort")
		sort_value = param
	})

	$inspect(sort_value)
</script>

{#if browser}
	<!-- if javascript, we can do whatever we want \o/ -->
	<label for="sort">ordered by</label>
	<select
		id="sort"
		aria-label="Sort nodes"
		onchange={(e) => {
			e.preventDefault()
			const select = e.currentTarget as HTMLSelectElement
			sort_value = select.value!

			replaceState(url_with_sort(sort_value), {
				node: sort_value ? sort_value : undefined
			})
		}}
	>
		{#each sorts as sort_option, index}
			<option
				value={sort_option.key}
				selected={(index === 0 && !sort_value) ||
					sort_option.key === sort_value}
			>
				{sort_option.value}
			</option>
		{/each}
	</select>
{:else}
	<!-- if server we rendered selects can't do actions on change. fall back on links -->
	<div class="chips">
		ordered by
		{#each sorts as sort_option}
			<a
				href={url_with_sort(sort_option.key)}
				aria-current={sort_option.key === sort_value ? "page" : undefined}
				>{sort_option.value}</a
			>
		{/each}
	</div>
{/if}

<style>
	select {
		margin: 0;
	}

	select,
	.chips a {
		font-size: 0.8em;
	}

	.chips {
		display: inline-flex;
		align-items: center;
		flex-wrap: wrap;
		gap: 0.5ch;
		padding: 0;
		list-style-type: none;
	}

	.chips a {
		line-height: 1;
		flex-basis: 0;
		padding: 0.25em 0.25em;
		white-space: nowrap;
		box-sizing: border-box;
		border: 1px solid var(--color-border);
		background-color: var(--color-bg-secondary);
		color: var(--color-text);
		text-decoration: none;
		font-family: "Fantasque Sans Mono", monospace;
	}

	.chips a[aria-current="page"] {
		border-color: var(--color-primary);
		background-color: var(--color-primary);
		color: var(--color-text-primary);
		font-weight: bold;
	}
</style>
