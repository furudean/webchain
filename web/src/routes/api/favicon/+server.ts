import { text } from "@sveltejs/kit"
import type { RequestHandler } from "./$types"
import {
	get_cached_file,
	cache_empty_favicon,
	is_stale_but_valid,
	fetch_and_cache_favicon,
	refresh_favicon_in_background,
	type CachedItem,
	STALE_THRESHOLD_MS
} from "$lib/favicon"
import { is_valid_url } from "$lib/url"
import pixel from "./1x1.png?arraybuffer"
import { robots_ok, is_webchain_node } from "$lib/crawler"
import { compress_if_accepted } from "$lib/compress"

function response_headers({
	item,
	allowed_origin
}: {
	item: CachedItem
	allowed_origin: string
	is_stale?: boolean
}): Headers {
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

	const ttl = Math.max(0, Math.floor(item.expires / 1000))
	headers.set(
		"Cache-Control",
		`public, max-age=${ttl}, stale-while-revalidate=${STALE_THRESHOLD_MS / 1000}`
	)
	headers.set("Expires", new Date(item.expires).toUTCString())

	headers.set("Access-Control-Allow-Origin", allowed_origin)

	return headers
}

async function create_empty_response({
	url,
	origin,
	request,
	fallback_url,
	disk_cache_status = "MISS"
}: {
	url: string
	origin: string
	request?: Request
	fallback_url?: string | null
	disk_cache_status?: string
}): Promise<Response> {
	if (fallback_url) {
		const headers = new Headers()
		headers.set("Location", fallback_url)
		headers.set("Access-Control-Allow-Origin", origin)
		return new Response(null, {
			status: 302,
			headers
		})
	}
	const item = cache_empty_favicon(url)
	const image = pixel
	const { body, encoding } = request
		? await compress_if_accepted(image, request)
		: { body: image }

	const headers = response_headers({ item, allowed_origin: origin })
	headers.set("content-type", "image/png")
	headers.set("x-disk-cache", disk_cache_status)
	if (encoding) {
		headers.set("Content-Encoding", encoding)
	}

	const response_body = body instanceof Uint8Array ? Buffer.from(body) : body
	return new Response(response_body, {
		status: 200,
		headers
	})
}

async function compressed_response({
	data,
	item,
	request,
	origin,
	is_stale
}: {
	data: ArrayBuffer | Uint8Array | Buffer
	item: CachedItem
	request: Request
	origin: string
	is_stale?: boolean
}): Promise<Response> {
	const binary = data instanceof ArrayBuffer ? new Uint8Array(data) : data
	const { body, encoding } = await compress_if_accepted(binary, request)
	const headers = response_headers({ item, allowed_origin: origin })
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

export const OPTIONS: RequestHandler = async ({ url }) => {
	const headers = new Headers()
	headers.set("Access-Control-Allow-Origin", url.origin)
	headers.set("Access-Control-Allow-Methods", "*")
	headers.set("Access-Control-Allow-Headers", "*")
	return new Response(null, {
		status: 204,
		headers
	})
}

export const GET: RequestHandler = async ({ url, fetch, request }) => {
	const url_param = url.searchParams.get("url")
	const fallback_url = url.searchParams.get("fallback")

	if (!url_param) {
		return text("url parameter required", { status: 400 })
	}

	if (!is_valid_url(url_param)) {
		return text("invalid url parameter", { status: 400 })
	}

	if (!(await is_webchain_node(url_param, fetch))) {
		return text("nice try, but i thought about that", { status: 400 })
	}

	if (!(await robots_ok(url_param, fetch))) {
		return text("website disallows crawling", { status: 400 })
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
			const headers = response_headers({
				item,
				allowed_origin: url.origin,
				is_stale
			})
			headers.set("x-disk-cache", is_stale ? "STALE" : "HIT")
			return new Response(null, {
				status: 304,
				headers
			})
		}

		if (!data) {
			return await create_empty_response({
				url: url_param,
				origin: url.origin,
				request,
				fallback_url,
				disk_cache_status: is_stale ? "STALE" : "HIT"
			})
		}

		return await compressed_response({
			data,
			item,
			origin: url.origin,
			request,
			is_stale
		})
	}

	const fetch_result = await fetch_and_cache_favicon(url_param, fetch)
	if (!fetch_result) {
		return await create_empty_response({
			url: url_param,
			origin: url.origin,
			request,
			fallback_url
		})
	}

	return await compressed_response({
		data: fetch_result.data,
		item: fetch_result.item,
		request,
		origin: url.origin,
		is_stale: false
	})
}
