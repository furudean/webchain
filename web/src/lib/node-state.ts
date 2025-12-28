import { writable } from "svelte/store"
import { replaceState } from "$app/navigation"
import { page } from "$app/state"

export const hovered_node = writable<string | undefined>(undefined)

export async function set_highlighted_node(
	node: string | undefined,
	url_param: string | undefined = undefined
) {
	const url = new URL(page.url)

	if (node && url_param) {
		url.searchParams.set("node", url_param)
	} else {
		url.searchParams.delete("node")
	}

	// eslint-disable-next-line svelte/no-navigation-without-resolve
	replaceState("?" + url.searchParams.toString(), {
		node
	})
}
