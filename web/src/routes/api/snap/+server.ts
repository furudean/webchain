import type { RequestHandler } from "./$types"
import { is_valid_url } from "$lib/url"
import { text } from "@sveltejs/kit"
import { compress_if_accepted } from "$lib/compress"
import { get_webchain_urls } from "$lib/crawler"

import {
	get_cached_snap,
	type SnapSidecar,
	atomic_fetch_and_cache_snap
} from "$lib/snap"

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

interface MakeSnapResponseParams {
	data: Buffer | null
	sidecar: SnapSidecar
	disk_cache: "HIT" | "MISS"
	request: Request
	url_origin: string
	not_modified?: boolean
	no_cache?: boolean
	stale?: boolean
}

async function make_snap_response({
	data,
	sidecar,
	disk_cache,
	request,
	url_origin,
	not_modified = false,
	no_cache = false,
	stale = false
}: MakeSnapResponseParams): Promise<Response> {
	const headers = new Headers()
	headers.set("ETag", sidecar.etag)
	headers.set("Access-Control-Allow-Origin", url_origin)
	headers.set("x-disk-cache", disk_cache)

	const ttl = Math.max(0, Math.floor((sidecar.expires - Date.now()) / 1000))

	if (no_cache) {
		headers.set(
			"Cache-Control",
			"no-store, no-cache, must-revalidate, proxy-revalidate"
		)
		headers.set("Pragma", "no-cache")
		headers.set("Expires", "0")
	} else if (stale) {
		headers.set(
			"Cache-Control",
			`public, max-age=0, must-revalidate, stale-while-revalidate=300`
		)
		headers.set("Expires", new Date(sidecar.expires).toUTCString())
	} else {
		headers.set(
			"Cache-Control",
			`public, max-age=${ttl}, stale-while-revalidate=300`
		)
		headers.set("Expires", new Date(sidecar.expires).toUTCString())
	}

	if (not_modified) {
		return new Response(null, { status: 304, headers })
	}
	headers.set("Content-Type", sidecar.content_type)
	if (data) {
		const { body, encoding } = await compress_if_accepted(data, request)
		if (encoding) headers.set("Content-Encoding", encoding)
		return new Response(
			Buffer.from(body instanceof ArrayBuffer ? new Uint8Array(body) : body),
			{ headers }
		)
	}
	return new Response(null, { status: 500, headers })
}

export const GET: RequestHandler = async ({ url, request, fetch }) => {
	const url_param = url.searchParams.get("url")
	const force_refresh = url.searchParams.has("refresh")

	if (!url_param) {
		return text("url parameter required", { status: 400 })
	}

	if (!is_valid_url(url_param)) {
		return text("invalid url parameter", { status: 400 })
	}

	if (!(await get_webchain_urls(fetch))) {
		return text("nice try, but i thought about that", { status: 400 })
	}

	if (!force_refresh) {
		const cache_hit = await get_cached_snap(url_param)
		const if_none_match = request.headers.get("if-none-match")

		if (cache_hit) {
			const { data, sidecar, expired } = cache_hit
			if (sidecar.etag && if_none_match === sidecar.etag && !expired) {
				return await make_snap_response({
					data: null,
					sidecar,
					disk_cache: "HIT",
					request,
					url_origin: url.origin,
					not_modified: true
				})
			}
			if (!expired) {
				return await make_snap_response({
					data,
					sidecar,
					disk_cache: "HIT",
					request,
					url_origin: url.origin
				})
			}

			// serve stale cache, queue background refresh
			atomic_fetch_and_cache_snap(url_param).catch((err) => {
				console.error("failed to refresh screenshot for", url_param, err)
			})

			return await make_snap_response({
				data,
				sidecar,
				disk_cache: "HIT",
				request,
				url_origin: url.origin,
				stale: true
			})
		}
	}

	let fetch_result: Awaited<ReturnType<typeof atomic_fetch_and_cache_snap>>

	try {
		fetch_result = await atomic_fetch_and_cache_snap(url_param)
	} catch (err) {
		console.error("failed to fetch and cache snap for", url_param, err)
		if (err instanceof Response) return err
		return text("failed to capture screenshot", { status: 503 })
	}

	return await make_snap_response({
		data: fetch_result.data,
		sidecar: fetch_result.sidecar,
		disk_cache: "MISS",
		request,
		url_origin: url.origin,
		no_cache: force_refresh
	})
}
