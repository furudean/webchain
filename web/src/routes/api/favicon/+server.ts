import { text } from "@sveltejs/kit"
import type { RequestHandler } from "./$types"
import { parse } from "node-html-parser"
import type { HTMLElement } from "node-html-parser"
import {
	FAVICON_CACHE,
	get_cached_file,
	write_cache_file,
	type CachedItem
} from "$lib/image-cache"

function is_valid_url(str: string): boolean {
	let url: URL | undefined

	try {
		url = new URL(str)
	} catch {
		return false
	}

	return url.protocol === "http:" || url.protocol === "https:"
}

async function get_icon_urls(
	base: URL | string,
	head: HTMLElement | null
): Promise<URL[]> {
	// try common favicon link rels
	const selectors = ['link[rel="icon"]', 'link[rel="shortcut icon"]']
	const possible_icons: Set<URL> = new Set()

	if (head) {
		for (const selector of selectors) {
			const element = head.querySelector(selector)
			if (element?.hasAttribute("href")) {
				const href = element.getAttribute("href")!
				// first check if its a valid url on its own
				const valid_url = is_valid_url(href)
				if (valid_url) {
					possible_icons.add(new URL(href))
				} else {
					// if not, it's probably a relative url, try to resolve it
					try {
						possible_icons.add(new URL(href, base))
					} catch {
						// invalid url, skip
						console.log(`skipping invalid favicon url: ${href}`)
						continue
					}
				}
			}
		}
	}

	// try favicon.ico
	possible_icons.add(new URL("/favicon.ico", base))

	return Array.from(possible_icons.values())
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

function empty_response_cache(url: string): Response {
	const cache_duration = 10 * 60 * 1000 // 10 minutes in ms
	FAVICON_CACHE.set(url, {
		timestamp: Date.now(),
		expires: Date.now() + cache_duration
	})
	return new Response(null, {
		status: 204,
		headers: {
			"Cache-Control": `public, max-age=${cache_duration / 1000}`
		}
	})
}
let graph_url_cache: { data: string[]; expires: number } | null = null

async function list_graph_urls(get: typeof fetch): Promise<string[]> {
	const now = Date.now()
	if (graph_url_cache && graph_url_cache.expires > now) {
		return graph_url_cache.data
	}

	const request = await get("/crawler/data.json")

	if (!request.ok) {
		throw new Error("failed to fetch data graph")
	}

	try {
		const { nodes }: { nodes: { at: string }[] } = await request.json()
		const urls = nodes.map((node) => node.at)
		graph_url_cache = {
			data: urls,
			expires: now + 60_000 // 1 minute
		}
		return urls
	} catch (error) {
		console.error("error parsing JSON:", error)
		throw new Error("failed to parse data graph")
	}
}

async function log_page_fetch_error(response: Response): Promise<string> {
	const headers = Array.from(response.headers.entries())
		.map(([key, value]) => `  ${key}: ${value}`)
		.join("\n")

	return [
		`failed to fetch page ${response.url}`,
		`status: ${response.status} ${response.statusText}`,
		"headers:",
		headers,
		"response body:",
		(await response.text())?.slice(0, 500),
		"\n"
	].join("\n")
}

const request_headers = new Headers({
	"User-Agent":
		"webchain-favicon-fetcher/DRAFT (+https://webchain.milkmedicine.net)",
	"Accept-Language": "en-US, *;q=0.5"
})

export const GET: RequestHandler = async ({ url, fetch }) => {
	const url_param = url.searchParams.get("url")

	if (!url_param) {
		return text("url parameter required", { status: 400 })
	}

	if (!is_valid_url(url_param)) {
		return text("invalid url parameter", { status: 400 })
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

	// make sure the requested url is in the graph
	const graph_urls = await list_graph_urls(fetch)
	if (!graph_urls.includes(url_param)) {
		return text("nice try, but i thought about that", { status: 400 })
	}

	// not in cache, fetch it
	try {
		const page_response = await fetch(url_param, {
			redirect: "follow",
			headers: request_headers
		})

		if (!page_response.ok) {
			console.log(await log_page_fetch_error(page_response))
			return new Response(
				`failed not load ${url_param}: ${page_response.status} ${page_response.statusText}`,
				{ status: 422 }
			)
		}

		const html = parse(await page_response.text())
		if (!html) return empty_response_cache(url_param)

		const icon_urls = await get_icon_urls(url_param, html.querySelector("head"))
		if (icon_urls.length === 0) return empty_response_cache(url_param)

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
		if (!best_icon) return empty_response_cache(url_param)

		const buffer = await best_icon.arrayBuffer()
		const content_type = best_icon.headers.get("Content-Type") || "image/x-icon"

		const cache_item = await write_cache_file({
			key: url_param,
			data: buffer,
			content_type,
			file_url: best_icon.url
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
		return text(`failed to fetch favicon: ${error}`, { status: 500 })
	}
}
