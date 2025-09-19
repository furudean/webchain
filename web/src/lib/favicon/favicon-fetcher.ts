import type { CachedItem } from "./types"
import { FAVICON_CACHE_DURATION } from "./types"
import { write_cache_file } from "./storage"
import { parse_page_for_icons } from "./icon-discovery"

const favicon_fetch_promises = new Map<string, Promise<CachedItem | null>>()
const request_headers = new Headers({
	"User-Agent":
		"webchain-favicon-fetcher/DRAFT (+https://webchain.milkmedicine.net)",
	"Accept-Language": "en-US,en;q=0.9,*;q=0.5",
	Accept: "*/*"
})

export async function fetch_and_cache_favicon(
	url_param: string,
	fetch: typeof globalThis.fetch
): Promise<CachedItem | null> {
	const existing_promise = favicon_fetch_promises.get(url_param)
	if (existing_promise) {
		return existing_promise
	}

	const fetch_promise = (async (): Promise<CachedItem | null> => {
		try {
			const page_response = await fetch(url_param, {
				redirect: "follow",
				headers: request_headers
			})

			if (!page_response.ok) {
				console.log(
					`failed to fetch page ${url_param}: ${page_response.status}`
				)
				return null
			}

			const html = await page_response.text()
			const icon_urls = await parse_page_for_icons(url_param, html)
			if (icon_urls.length === 0) return null

			const icon_responses = await Promise.allSettled(
				icon_urls.map((icon_url) =>
					fetch(icon_url, {
						redirect: "follow",
						headers: request_headers
					})
				)
			)

			const best_icon = icon_responses.find(
				(result): result is PromiseFulfilledResult<Response> =>
					result.status === "fulfilled" && result.value.ok
			)?.value

			if (!best_icon) return null

			const buffer = await best_icon.arrayBuffer()
			const content_type =
				best_icon.headers.get("Content-Type") || "image/x-icon"

			return await write_cache_file({
				key: url_param,
				data: buffer,
				content_type,
				file_url: best_icon.url,
				expires: Date.now() + FAVICON_CACHE_DURATION
			})
		} catch (error) {
			console.error(`error fetching favicon for ${url_param}:`, error)
			return null
		} finally {
			favicon_fetch_promises.delete(url_param)
		}
	})()

	favicon_fetch_promises.set(url_param, fetch_promise)

	return fetch_promise
}

export async function refresh_favicon_in_background(
	url_param: string,
	fetch: typeof globalThis.fetch
): Promise<void> {
	try {
		console.log(`background refresh started for ${url_param}`)
		await fetch_and_cache_favicon(url_param, fetch)
		console.log(`background refresh completed for ${url_param}`)
	} catch (error) {
		console.error(`background refresh error for ${url_param}:`, error)
	}
}
