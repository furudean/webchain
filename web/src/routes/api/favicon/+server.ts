import { text } from "@sveltejs/kit"
import type { RequestHandler } from "./$types"
import { parse } from "node-html-parser"
import type { HTMLElement } from "node-html-parser"
import {
	CACHE_DURATION,
	FAVICON_CACHE,
	get_cached_file,
	write_cache_file,
	type CachedItem
} from "$lib/image-cache"

async function get_icon_url(
	base: URL | string,
	head: HTMLElement
): Promise<URL | undefined> {
	// try common favicon link rels
	const selectors = ['link[rel="icon"]', 'link[rel="shortcut icon"]']

	for (const selector of selectors) {
		const element = head.querySelector(selector)
		if (element?.hasAttribute("href")) {
			const href = element.getAttribute("href")!
			try {
				return new URL(href, base)
			} catch {
				continue
			}
		}
	}

	// try favicon.ico
	const url = new URL("/favicon.ico", base)
	const result = await fetch(url, {
		method: "HEAD",
		redirect: "follow"
	})

	if (result.ok) {
		return url
	}

	return undefined
}

function response_headers(item: CachedItem): Record<string, string> {
	const headers: Record<string, string> = {}

	if (item.content_type) {
		headers["Content-Type"] = item.content_type
	}
	if (item.original_url) {
		headers["X-Original-URL"] = item.original_url
	}
	headers["Cache-Control"] =
		`public, max-age=${Math.min(0, Math.floor((item.expires - Date.now()) / 1000))}`

	return headers
}

function empty_response(url: string): Response {
	FAVICON_CACHE.set(url, {
		timestamp: Date.now(),
		expires: Date.now() + CACHE_DURATION
	})
	return new Response(null, {
		status: 204,
		headers: {
			"Cache-Control": `public, max-age=${CACHE_DURATION / 1000}`
		}
	})
}

export const GET: RequestHandler = async ({ url }) => {
	const url_param = url.searchParams.get("url")

	if (!url_param) {
		return text("url parameter required", { status: 400 })
	}

	// handle disk cache
	const cache_hit = await get_cached_file(url_param)
	if (cache_hit?.data) {
		return new Response(cache_hit.data, {
			status: 200,
			headers: {
				...response_headers(cache_hit.item),
				"x-disk-cache": "HIT"
			}
		})
	} else if (cache_hit) {
		return new Response(null, {
			status: 204,
			headers: {
				...response_headers(cache_hit.item),
				"x-disk-cache": "HIT"
			}
		})
	}

	// not in cache, fetch it
	try {
		const page_response = await fetch(url_param, {
			redirect: "follow"
		})

		if (!page_response.ok) empty_response(url_param)

		const page_url = page_response.url
		const html = parse(await page_response.text())
		const head = html.querySelector("head")

		if (head === null) return empty_response(url_param)

		const icon_url = await get_icon_url(page_url, head)
		if (!icon_url) return empty_response(url_param)

		const icon_response = await fetch(icon_url)
		if (!icon_response.ok) return empty_response(url_param)

		const buffer = await icon_response.arrayBuffer()
		const content_type =
			icon_response.headers.get("Content-Type") || "image/x-icon"

		const cache_item = await write_cache_file({
			key: url_param,
			data: buffer,
			content_type,
			file_url: icon_url.toString()
		})

		return new Response(buffer, {
			status: 200,
			headers: {
				...response_headers(cache_item),
				"x-disk-cache": "MISS"
			}
		})
	} catch (error) {
		console.error(`error fetching favicon for ${url_param}`, error)
		return text("failed to fetch favicon", { status: 500 })
	}
}
