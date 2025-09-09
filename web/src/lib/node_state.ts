import { writable } from "svelte/store"
import type GraphType from "graphology"
import { goto } from "$app/navigation"
import { page } from "$app/state"

export const hovered_node = writable<string | undefined>(undefined)
export const graph = writable<GraphType>(undefined)

export async function set_highlighted_node(node: string | undefined) {
	const url = new URL(page.url)
	if (node) {
		url.searchParams.set("node", node)
	} else {
		url.searchParams.delete("node")
	}
	await goto("?" + url.searchParams, {
		state: { node },
		replaceState: true,
		keepFocus: true,
		noScroll: true
	})
}
