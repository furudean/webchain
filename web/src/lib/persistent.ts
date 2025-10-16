import { writable } from "svelte/store"

type StorageType = "localStorage" | "sessionStorage"

export interface PersistentOptions<T> {
	start_value: T
	key: string
	storage_type: StorageType
	serialize?: (value: T) => string
	deserialize?: (value: string) => T
}

const DEFAULT_OPTIONS = Object.freeze({
	serialize: JSON.stringify,
	deserialize: JSON.parse
})

export function persistent<T>(options: PersistentOptions<T>) {
	const { key, storage_type, start_value, serialize, deserialize } = {
		...DEFAULT_OPTIONS,
		...options
	}

	const storage =
		typeof window !== "undefined"
			? (window[storage_type] as Storage | undefined)
			: undefined

	const store = writable<T>(start_value, function start() {
		function storage_handler(event: StorageEvent) {
			if (event.key === key) sync()
		}

		if (!storage) return

		sync()

		window.addEventListener("storage", storage_handler)

		return function stop() {
			window.removeEventListener("storage", storage_handler)
		}
	})

	function set(value: T) {
		store.set(value)
		storage?.setItem(key, serialize(value))
	}

	function update(updater: (value: T) => T) {
		store.update((current_value) => {
			const new_value = updater(current_value)
			storage?.setItem(key, serialize(new_value))
			return new_value
		})
	}

	function sync() {
		const stored_data = storage?.getItem(key)
		if (stored_data === null || stored_data === undefined) {
			set(start_value)
		} else {
			store.set(deserialize(stored_data))
		}
	}

	return {
		set,
		update,
		subscribe: store.subscribe
	}
}
