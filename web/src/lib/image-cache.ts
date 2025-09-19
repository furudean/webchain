import path from "node:path"
import fs from "node:fs/promises"
import { parse } from "node-html-parser"
import type { HTMLElement } from "node-html-parser"
import { createHash } from "crypto"
import {
	safe_read_file,
	safe_unlink,
	safe_access,
	safe_read_buffer
} from "./fs"

export interface CachedItem {
	path?: string
	timestamp: number
	expires: number
	content_type?: string
	original_url?: string
	etag?: string
}

export const CACHE_DIR = path.resolve(
	process.env.FAVICON_CACHE_DIR || path.join(process.cwd(), ".favicon_cache")
)
export const CACHE_INDEX_FILE = path.join(CACHE_DIR, "index.json")
export const FAVICON_CACHE_DURATION = 60 * 60 * 1000 // 1 hour
export const EMPTY_FAVICON_CACHE_DURATION = 10 * 60 * 1000 // 10 minutes
export const STALE_THRESHOLD = 60 * 60 * 1000 // 1 hour stale window
export const FAVICON_CACHE = new Map<string, CachedItem>()

// load cache index on startup
let cache_loading_promise: Promise<void> | null = null

function safe_parse_url(href: string, base: string | URL): URL | null {
	try {
		return new URL(href, base)
	} catch {
		return null
	}
}

async function load_cache_index(): Promise<void> {
	// if already loading, return the existing promise
	if (cache_loading_promise) {
		return cache_loading_promise
	}

	cache_loading_promise = (async () => {
		const index_content = await safe_read_file(CACHE_INDEX_FILE)
		if (!index_content) {
			// index file doesn't exist or is corrupted, start fresh
			cache_loading_promise = null
			return
		}

		const cache_data: Record<string, CachedItem> = JSON.parse(index_content)
		const now = Date.now()

		for (const [key, item] of Object.entries(cache_data)) {
			// handle expired items
			if (item.expires <= now) {
				if (item.path) {
					const fullpath = path.join(CACHE_DIR, item.path)
					await safe_unlink(fullpath)
				}
				continue
			}

			// handle empty cache items (no file)
			if (!item.path) {
				FAVICON_CACHE.set(key, item)
				continue
			}

			// handle items with files - check if file exists
			const fullpath = path.join(CACHE_DIR, item.path)
			const file_exists = await safe_access(fullpath)
			if (file_exists) {
				FAVICON_CACHE.set(key, item)
			}
		}

		console.log(`loaded favicon cache with ${FAVICON_CACHE.size} entries`)
	})()

	return cache_loading_promise
}

async function save_cache_index(): Promise<void> {
	await fs.mkdir(CACHE_DIR, { recursive: true })
	const cache_data = Object.fromEntries(FAVICON_CACHE.entries())
	await fs.writeFile(CACHE_INDEX_FILE, JSON.stringify(cache_data, null, "\t"))
}

function to_array_buffer(buffer: Buffer): ArrayBuffer {
	const array_buffer = new ArrayBuffer(buffer.length)
	const view = new Uint8Array(array_buffer)
	for (let i = 0; i < buffer.length; ++i) {
		view[i] = buffer[i]
	}
	return array_buffer
}

export function generate_etag(data: ArrayBufferLike): string {
	return (
		'"' +
		createHash("sha256")
			.update(new Uint8Array(data))
			.digest("hex")
			.slice(0, 16) +
		'"'
	)
}

export async function write_cache_file({
	key,
	data,
	content_type,
	file_url,
	expires = undefined
}: {
	key: string
	data: ArrayBufferLike
	content_type: string
	file_url: string
	expires?: number
}): Promise<CachedItem> {
	await load_cache_index()

	const filename = encodeURIComponent(key)
	const fullpath = path.join(CACHE_DIR, filename)

	// ensure cache directory exists
	await fs.mkdir(CACHE_DIR, { recursive: true })
	await fs.writeFile(fullpath, Buffer.from(data))

	const item = {
		path: filename,
		timestamp: Date.now(),
		expires: expires ?? Date.now() + FAVICON_CACHE_DURATION,
		original_url: file_url,
		content_type,
		etag: generate_etag(data)
	}

	FAVICON_CACHE.set(key, item)

	await save_cache_index()

	return item
}

/**
 * retrieves a cached file from the favicon cache
 *
 * @returns the cache entry, or `null` if the cache entry is explicitly null,
 * or `undefined` if the cache entry is missing or expired.
 */
export async function get_cached_file(key: string): Promise<
	| {
			data: ArrayBuffer | undefined
			item: CachedItem
	  }
	| undefined
> {
	await load_cache_index()

	const cached = FAVICON_CACHE.get(key)

	if (cached) {
		if (cached.expires < Date.now()) {
			FAVICON_CACHE.delete(key)
			// delete the file if it exists
			if (cached.path) {
				const fullpath = path.join(CACHE_DIR, cached.path)
				await safe_unlink(fullpath)
			}
			return undefined
		}

		if (cached?.path) {
			const fullpath = path.join(CACHE_DIR, cached.path)
			const buffer = await safe_read_buffer(fullpath)
			if (buffer) {
				return {
					data: to_array_buffer(buffer),
					item: cached
				}
			} else {
				FAVICON_CACHE.delete(key)
			}
		} else {
			// cached as empty
			return {
				data: undefined,
				item: cached
			}
		}
	}

	return undefined
}

export function is_valid_url(str: string): boolean {
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
					const parsed_url = safe_parse_url(href, base)
					if (parsed_url) {
						possible_icons.add(parsed_url)
					} else {
						console.log(`skipping invalid favicon url: ${href}`)
					}
				}
			}
		}
	}

	// try favicon.ico
	possible_icons.add(new URL("/favicon.ico", base))

	return Array.from(possible_icons.values())
}

export function is_stale_but_valid(item: CachedItem): boolean {
	const now = Date.now()
	return item.expires < now && now - item.expires < STALE_THRESHOLD
}

export async function cleanup_expired_cache(): Promise<void> {
	await load_cache_index()

	const now = Date.now()
	let cleaned_count = 0

	for (const [key, item] of FAVICON_CACHE.entries()) {
		if (item.expires + STALE_THRESHOLD < now) {
			FAVICON_CACHE.delete(key)

			// also remove the file if it exists
			if (item.path) {
				const fullpath = path.join(CACHE_DIR, item.path)
				await safe_unlink(fullpath)
			}

			cleaned_count++
		}
	}

	if (cleaned_count > 0) {
		console.log(`cleaned up ${cleaned_count} expired cache entries`)
		await save_cache_index()
	}
}

// track ongoing favicon fetches to avoid duplicates
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
	// check if we're already fetching this favicon
	const existing_promise = favicon_fetch_promises.get(url_param)
	if (existing_promise) {
		return existing_promise
	}

	// create and track the fetch promise
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

			const html = parse(await page_response.text())
			if (!html) return null

			const icon_urls = await get_icon_urls(
				url_param,
				html.querySelector("head")
			)
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
			// clean up the promise tracking
			favicon_fetch_promises.delete(url_param)
		}
	})()

	// track the promise
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

export function cache_empty_favicon(url: string): CachedItem {
	const item = {
		timestamp: Date.now(),
		expires: Date.now() + EMPTY_FAVICON_CACHE_DURATION
	}
	FAVICON_CACHE.set(url, item)

	// save index after adding empty cache entry
	save_cache_index().catch(console.error)

	return item
}
