import { text } from "@sveltejs/kit"
import type { RequestHandler } from "./$types"
import {
	get_cached_file,
	cache_empty_favicon,
	is_stale_but_valid,
	fetch_and_cache_favicon,
	refresh_favicon_in_background,
	type CachedItem
} from "$lib/favicon"
import { is_valid_url } from "$lib/url"

function response_headers(
	item: CachedItem,
	is_stale?: boolean
): Record<string, string> {
	const headers = new URLSearchParams()

	if (item.content_type) {
		headers.set("Content-Type", item.content_type)
	}
	if (item.original_url) {
		headers.set("X-Original-URL", item.original_url)
	}
	if (item.etag) {
		headers.set("ETag", item.etag)
	}

	if (is_stale) {
		headers.set(
			"Cache-Control",
			"public, max-age=0, stale-while-revalidate=3600"
		)
	} else {
		headers.set("Cache-Control", "public, max-age=3600") // Add explicit max-age
		if (item.expires) {
			headers.set("Expires", new Date(item.expires).toUTCString())
		}
	}

	return Object.fromEntries(headers.entries())
}

function create_empty_response(
	url: string,
	cache_status: string = "MISS"
): Response {
	const item = cache_empty_favicon(url)
	return new Response(null, {
		status: 204,
		headers: {
			...response_headers(item),
			"x-disk-cache": cache_status
		}
	})
}

export const GET: RequestHandler = async ({ url, fetch, request }) => {
	const url_param = url.searchParams.get("url")

	if (!url_param) {
		return text("url parameter required", { status: 400 })
	}

	if (!is_valid_url(url_param)) {
		return text("invalid url parameter", { status: 400 })
	}

	// handle disk cache with stale-while-revalidate
	const cache_hit = await get_cached_file(url_param)
	if (cache_hit) {
		const { data, item } = cache_hit
		const if_none_match = request.headers.get("if-none-match")
		const is_stale = is_stale_but_valid(item)

		// console.debug(`favicon cache hit for ${url_param}:`, {
		// 	is_stale,
		// 	expires: item.expires,
		// 	now: Date.now(),
		// 	expires_in: item.expires ? item.expires - Date.now() : null,
		// 	stale_in: item.stale_after ? item.stale_after - Date.now() : null
		// })

		// trigger background refresh for stale content once
		if (is_stale) {
			refresh_favicon_in_background(url_param, fetch).catch(console.error)
		}

		// handle conditional requests
		if (item.etag && if_none_match === item.etag) {
			// not modified
			return new Response(null, {
				status: 304,
				headers: {
					ETag: item.etag,
					"Cache-Control": is_stale
						? "public, max-age=0, stale-while-revalidate=3600"
						: "public",
					"x-disk-cache": is_stale ? "STALE" : "HIT"
				}
			})
		}

		if (!data) {
			// return cached content (data or empty)
			return create_empty_response(url_param, is_stale ? "STALE" : "HIT")
		}

		return new Response(data, {
			status: 200,
			headers: {
				...response_headers(item, is_stale),
				"x-disk-cache": is_stale ? "STALE" : "HIT"
			}
		})
	}

	// not in cache, fetch it
	const fetch_result = await fetch_and_cache_favicon(url_param, fetch)
	if (!fetch_result) {
		return create_empty_response(url_param)
	}

	return new Response(fetch_result.data, {
		status: 200,
		headers: {
			...response_headers(fetch_result.item),
			"x-disk-cache": "MISS"
		}
	})
}
