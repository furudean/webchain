import { text } from "@sveltejs/kit"
import type { RequestHandler } from "./$types"
import { parse } from "node-html-parser"
import type { HTMLElement } from "node-html-parser"
import { CACHE_DURATION, FAVICON_CACHE, get_cached_file, write_cache_file, type CachedItem } from "$lib/cache"

async function get_icon_url(
	base: URL | string,
	head: HTMLElement
): Promise<URL | undefined> {
	const selectors = [
		'link[rel="icon"]',
		'link[rel="shortcut icon"]'
	]

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
	return {
		"Content-Type": item.content_type!,
		"Cache-Control": `public, max-age=${Math.floor((item.expires - Date.now()) / 1000)}`,
		"X-Original-URL": item.original_url!
	}
}

function empty_response(url: string): Response {
	FAVICON_CACHE.set(url, {
		timestamp: Date.now(),
		expires: Date.now() + CACHE_DURATION,
	})
	return new Response(null, { status: 204, headers: {
		"Cache-Control": `public, max-age=${CACHE_DURATION / 1000}`
	} })
}

export const GET: RequestHandler = async ({ url }) => {
	const url_param = url.searchParams.get("url")

	if (!url_param) {
		return text("url parameter required", { status: 400 })
	}

	// handle disk cache
	const cache_item = await get_cached_file(url_param)
	if (cache_item) {
		return new Response(cache_item.data, {
			status: 200,
			headers: {
				...response_headers(cache_item.item),
				'x-disk-cache': 'HIT'
			}
		})
	} else if (cache_item === null) {
		const response = empty_response(url_param)
		response.headers.set('x-disk-cache', 'HIT')
		return response
	}

	// not in cache, fetch it
	try {
		const page_response = await fetch(url_param, {
			redirect: "follow"
		})

		if (!page_response.ok) {
			return new Response(null, { status: 204 })
		}

		const page_url = page_response.url
		const html = parse(await page_response.text())
		const head = html.querySelector("head")

		if (head === null) return empty_response(url_param)

		const icon_url = await get_icon_url(page_url, head)
		if (!icon_url) return empty_response(url_param)

		const icon_response = await fetch(icon_url)
		if (!icon_response.ok) return new Response(null, { status: 204 })

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
				'x-disk-cache': 'MISS'
			}
		})
	} catch (error) {
		console.error("error fetching favicon:", error)
		return text("failed to fetch favicon", { status: 500 })
	}
}
