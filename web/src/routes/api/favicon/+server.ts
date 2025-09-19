import { text } from "@sveltejs/kit"
import type { RequestHandler } from "./$types"
import {
	get_cached_file,
	fetch_and_cache_favicon,
	refresh_favicon_in_background,
	cache_empty_favicon,
	is_stale_but_valid,
	is_valid_url,
	type CachedItem
} from "$lib/image-cache"

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
		headers.set("Cache-Control", "public")
		headers.set("Expires", new Date(item.expires).toUTCString())
	}

	return Object.fromEntries(headers.entries())
}

function empty_response_cache(url: string): Response {
	const item = cache_empty_favicon(url)
	return new Response(null, {
		status: 204,
		headers: {
			"Cache-Control": "public",
			Expires: new Date(item.expires).toUTCString()
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

		// handle conditional requests
		if (item.etag && if_none_match === item.etag) {
			if (is_stale) {
				refresh_favicon_in_background(url_param, fetch).catch(console.error)
			}
			return new Response(null, {
				status: 304,
				headers: {
					ETag: item.etag,
					"Cache-Control": is_stale
						? "public, max-age=0, stale-while-revalidate=3600"
						: "public",
					"x-disk-cache": "HIT"
				}
			})
		}

		// trigger background refresh for stale content
		if (is_stale) {
			refresh_favicon_in_background(url_param, fetch).catch(console.error)
		}

		// return cached content (data or empty)
		return new Response(data || null, {
			status: data ? 200 : 204,
			headers: {
				...response_headers(item, is_stale),
				"x-disk-cache": is_stale ? "STALE" : "HIT"
			}
		})
	}

	// not in cache, fetch it
	const cache_item = await fetch_and_cache_favicon(url_param, fetch)
	if (!cache_item) {
		return empty_response_cache(url_param)
	}

	// Return the newly cached item directly
	const fresh_cache_hit = await get_cached_file(url_param)
	if (!fresh_cache_hit?.data) {
		return empty_response_cache(url_param)
	}

	return new Response(fresh_cache_hit.data, {
		status: 200,
		headers: {
			...response_headers(cache_item),
			"x-disk-cache": "MISS"
		}
	})
}
