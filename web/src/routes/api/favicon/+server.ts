import { text } from "@sveltejs/kit"
import type { RequestHandler } from "./$types"
import {
	get_cached_file,
	cache_empty_favicon,
	is_stale_but_valid,
	fetch_and_cache_favicon,
	refresh_favicon_in_background,
	type CachedItem,
	FAVICON_CACHE_DURATION,
	STALE_THRESHOLD
} from "$lib/favicon"
import { is_valid_url } from "$lib/url"
import { gzipSync, deflateSync } from "node:zlib"

function response_headers(item: CachedItem, is_stale?: boolean): Headers {
	const headers = new Headers()

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
			`public, max-age=0, stale-while-revalidate=${STALE_THRESHOLD}`
		)
	} else {
		headers.set("Cache-Control", `public, max-age=${FAVICON_CACHE_DURATION}`)
		if (item.expires) {
			headers.set("Expires", new Date(item.expires).toUTCString())
		}
	}

	return headers
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

async function compress_if_accepted(
	data: Uint8Array | Buffer,
	request: Request
): Promise<{ body: Uint8Array | Buffer; encoding?: string }> {
	const acceptEncoding = request.headers.get("accept-encoding") || ""
	if (/\bgzip\b/.test(acceptEncoding)) {
		return {
			body: gzipSync(data),
			encoding: "gzip"
		}
	}
	if (/\bdeflate\b/.test(acceptEncoding)) {
		return {
			body: deflateSync(data),
			encoding: "deflate"
		}
	}
	return { body: data }
}

async function compressed_response({
	data,
	item,
	request,
	is_stale
}: {
	data: ArrayBuffer | Uint8Array | Buffer
	item: CachedItem
	request: Request
	is_stale?: boolean
}): Promise<Response> {
	const binary = data instanceof ArrayBuffer ? new Uint8Array(data) : data
	const { body, encoding } = await compress_if_accepted(binary, request)
	const headers = response_headers(item, is_stale)
	headers.set("x-disk-cache", is_stale ? "STALE" : "HIT")
	if (encoding) {
		headers.set("Content-Encoding", encoding)
	}
	const response_body =
		body instanceof Uint8Array || Buffer.isBuffer(body)
			? Buffer.from(body)
			: body
	return new Response(response_body, {
		status: 200,
		headers
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

	const cache_hit = await get_cached_file(url_param)
	if (cache_hit) {
		const { data, item } = cache_hit
		const if_none_match = request.headers.get("if-none-match")
		const is_stale = is_stale_but_valid(item)

		if (is_stale) {
			refresh_favicon_in_background(url_param, fetch).catch(console.error)
		}

		if (item.etag && if_none_match === item.etag) {
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
			return create_empty_response(url_param, is_stale ? "STALE" : "HIT")
		}

		return await compressed_response({
			data,
			item,
			request,
			is_stale
		})
	}

	const fetch_result = await fetch_and_cache_favicon(url_param, fetch)
	if (!fetch_result) {
		return create_empty_response(url_param)
	}

	return await compressed_response({
		data: fetch_result.data,
		item: fetch_result.item,
		request,
		is_stale: false
	})
}
