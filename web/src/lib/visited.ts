import { browser } from "$app/environment"
import { persistent } from "./persistent"
import type { Writable } from "svelte/store"

function create_visited_store(): Writable<Date | null> {
	const { subscribe, set, update } = persistent<Date | null>({
		key: "last-visited",
		start_value: null,
		storage_type: "localStorage",
		serialize: (date) => (date ? date.toISOString() : ""),
		deserialize: (str) => (str ? new Date(str) : null)
	})

	if (browser) {
		window.addEventListener("beforeunload", () => {
			set(new Date())
		})
	}

	return {
		subscribe,
		set,
		update
	}
}

export const last_visited = create_visited_store()
