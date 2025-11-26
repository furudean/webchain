import { write_cache_file } from "./storage"
import { parse_page_for_icons } from "./icon-discovery"
import { FAVICON_CACHE_DURATION_MS, type CachedItem } from "."

const favicon_fetch_promises = new Map<
	string,
	Promise<{ data: ArrayBuffer; item: CachedItem } | null>
>()
const request_headers = new Headers({
	"User-Agent": "WebchainSpider (+https://github.com/furudean/webchain)",
	"Accept-Language": "en-US,en;q=0.9,*;q=0.5",
	Accept: "*/*"
})

const MAX_REQUESTS_PER_HOUR = 3
const request_timestamps_per_url = new Map<string, number[]>()

function can_make_request(url_param: string): boolean {
	const now = Date.now()
	const timestamps = request_timestamps_per_url.get(url_param) || []
	const recent = timestamps.filter((ts) => now - ts < 60 * 60 * 1000)
	request_timestamps_per_url.set(url_param, recent)
	return recent.length < MAX_REQUESTS_PER_HOUR
}

function record_request(url_param: string) {
	const now = Date.now()
	const timestamps = request_timestamps_per_url.get(url_param) || []
	timestamps.push(now)
	request_timestamps_per_url.set(url_param, timestamps)
}

export async function fetch_and_cache_favicon(
	url_param: string,
	fetch: typeof globalThis.fetch
): Promise<{ data: ArrayBuffer; item: CachedItem } | null> {
	if (!can_make_request(url_param)) {
		console.warn("favicon fetch rate limit exceeded for", url_param)
		return null
	}
	record_request(url_param)

	const existing_promise = favicon_fetch_promises.get(url_param)
	if (existing_promise) {
		return existing_promise
	}

	const fetch_promise = (async (): Promise<{
		data: ArrayBuffer
		item: CachedItem
	} | null> => {
		try {
			const controller = new AbortController()
			const timeout = setTimeout(() => controller.abort(), 10_000)

			let page_response: Response
			try {
				page_response = await fetch(url_param, {
					redirect: "follow",
					headers: request_headers,
					signal: controller.signal
				})
			} catch (err) {
				if ((err as Error).name === "AbortError") {
					console.log(`fetch for ${url_param} timed out`)
					return null
				}
				throw err
			} finally {
				clearTimeout(timeout)
			}

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

			const cache_item = await write_cache_file({
				key: url_param,
				data: buffer,
				content_type,
				file_url: best_icon.url,
				expires: Date.now() + FAVICON_CACHE_DURATION_MS
			})

			return { data: buffer, item: cache_item }
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
		const already_running = favicon_fetch_promises.has(url_param)
		if (!already_running) {
			console.log(`favicon background refresh started for ${url_param}`)
		}
		await fetch_and_cache_favicon(url_param, fetch)
		if (!already_running) {
			console.log(`favicon background refresh completed for ${url_param}`)
		}
	} catch (error) {
		console.error(`favicon background refresh failed for ${url_param}:`, error)
	}
}
