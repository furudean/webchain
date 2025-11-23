import { vacuum_cache } from "$lib/snap"
import type { ServerInit } from "@sveltejs/kit"

export const init: ServerInit = async () => {
	// periodically clean up expired cache files every hour
	vacuum_cache()
		.then(() => {
			console.log("initial cache cleanup complete")
		})
		.catch((err) => console.error("initial cache cleanup error:", err))
	setInterval(
		() => {
			vacuum_cache().catch((err) =>
				console.error("periodic cache cleanup error:", err)
			)
		},
		24 * 60 * 60 * 1000
	)
}
