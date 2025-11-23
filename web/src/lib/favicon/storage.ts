import path from "node:path"
import fs from "node:fs/promises"
import { createHash } from "crypto"
import {
	safe_read_file,
	safe_unlink,
	safe_access,
	safe_read_buffer
} from "$lib/fs"
import {
	EMPTY_FAVICON_CACHE_DURATION,
	STALE_THRESHOLD,
	type CachedItem
} from "."
import { dev } from "$app/environment"
import env_paths from "env-paths"

const paths = env_paths("webchain-web-server")

const CACHE_DIR = path.join(dev ? process.cwd() : paths.cache, ".favicon_cache")
const CACHE_INDEX_FILE = path.join(CACHE_DIR, "index.json")
const FAVICON_CACHE = new Map<string, CachedItem>()

let cache_loading_promise: Promise<void> | null = null

console.log("storing favicon cache in:", CACHE_DIR)

function to_array_buffer(buffer: Buffer): ArrayBuffer {
	const array_buffer = new ArrayBuffer(buffer.length)
	const view = new Uint8Array(array_buffer)
	for (let i = 0; i < buffer.length; ++i) {
		view[i] = buffer[i]
	}
	return array_buffer
}

function generate_etag(data: ArrayBufferLike): string {
	const hash = createHash("sha256")
		.update(new Uint8Array(data))
		.digest("hex")
		.slice(0, 16)
	const quote = '"'

	return quote + hash + quote
}

export function is_stale_but_valid(item: CachedItem): boolean {
	const now = Date.now()
	return (
		item?.stale_after != null && item.stale_after < now && item.expires > now
	)
}

async function load_cache_index(): Promise<void> {
	if (cache_loading_promise) {
		return cache_loading_promise
	}

	async function load(): Promise<void> {
		const index_content = await safe_read_file(CACHE_INDEX_FILE)
		if (!index_content) return

		const cache_data: Record<string, CachedItem> = JSON.parse(index_content)
		const now = Date.now()

		for (const [key, item] of Object.entries(cache_data)) {
			if (item.expires <= now) {
				if (item.path) {
					const fullpath = path.join(CACHE_DIR, item.path)
					await safe_unlink(fullpath)
				}
				continue
			}

			if (!item.path) {
				FAVICON_CACHE.set(key, item)
				continue
			}

			const fullpath = path.join(CACHE_DIR, item.path)
			const file_exists = await safe_access(fullpath)
			if (file_exists) {
				FAVICON_CACHE.set(key, item)
			}
		}

		console.log(`loaded favicon cache with ${FAVICON_CACHE.size} entries`)
	}

	cache_loading_promise = load()

	return cache_loading_promise
}

async function save_cache_index(): Promise<void> {
	await fs.mkdir(CACHE_DIR, { recursive: true })
	const cache_data = Object.fromEntries(FAVICON_CACHE.entries())
	await fs.writeFile(CACHE_INDEX_FILE, JSON.stringify(cache_data, null, "\t"))
}

export async function write_cache_file({
	key,
	data,
	content_type,
	file_url,
	expires
}: {
	key: string
	data: ArrayBufferLike
	content_type: string
	file_url: string
	expires: number
}): Promise<CachedItem> {
	await load_cache_index()

	const filename = encodeURIComponent(key)
	const fullpath = path.join(CACHE_DIR, filename)

	await fs.mkdir(CACHE_DIR, { recursive: true })
	await fs.writeFile(fullpath, Buffer.from(data))

	const timestamp = Date.now()

	const item = {
		path: filename,
		timestamp,
		expires,
		stale_after: timestamp + STALE_THRESHOLD,
		original_url: file_url,
		content_type,
		etag: generate_etag(data)
	}

	FAVICON_CACHE.set(key, item)
	await save_cache_index()

	return item
}

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
			return {
				data: undefined,
				item: cached
			}
		}
	}

	return undefined
}

export function cache_empty_favicon(url: string): CachedItem {
	const item = {
		timestamp: Date.now(),
		expires: Date.now() + EMPTY_FAVICON_CACHE_DURATION
	}
	FAVICON_CACHE.set(url, item)

	save_cache_index().catch(console.error)

	return item
}
