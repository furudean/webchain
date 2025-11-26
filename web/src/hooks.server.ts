import {
	vacuum_cache as vacuum_snap_cache,
	fetch_and_cache_outdated_snaps,
	CACHE_DIR as SNAP_CACHE_DIR
} from "$lib/snap"
import fs from "fs/promises"
import type { ServerInit } from "@sveltejs/kit"
import {
	CACHE_DIR as FAVICON_CACHE_DIR,
	load_cache_index as load_favicon_cache
} from "$lib/favicon/storage"
import { building } from "$app/environment"

export const init: ServerInit = async () => {
	if (building) return

	await fs.mkdir(SNAP_CACHE_DIR, { recursive: true })
	console.log("storing snap cache in:", SNAP_CACHE_DIR)
	await fs.mkdir(FAVICON_CACHE_DIR, { recursive: true })
	console.log("storing favicon cache in:", FAVICON_CACHE_DIR)

	await load_favicon_cache()

	fetch_and_cache_outdated_snaps().catch((err) =>
		console.error("initial snap cache update error:", err)
	)

	// periodically check for expired cached snaps to refresh
	setInterval(
		() => {
			fetch_and_cache_outdated_snaps().catch((err) =>
				console.error("periodic snap cache update error:", err)
			)
		},
		10 * 60 * 1000 // every 10 minutes
	)

	// periodically clean up expired cache files
	setInterval(
		() => {
			vacuum_snap_cache().catch((err) =>
				console.error("periodic cache cleanup error:", err)
			)
		},
		7 * 24 * 60 * 60 * 1000 // every 7 days
	)
}
