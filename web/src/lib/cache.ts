import path from "node:path"
import fs from "node:fs/promises"

export interface CachedItem {
	path?: string
	timestamp: number
	expires: number
	content_type?: string
	original_url?: string
}

export const CACHE_DIR = path.resolve(".favicon_cache")
export const CACHE_DURATION = 24 * 60 * 60 * 1000
export const FAVICON_CACHE = new Map<string, CachedItem | null>()

function to_array_buffer(buffer: Buffer): ArrayBuffer {
	const array_buffer = new ArrayBuffer(buffer.length)
	const view = new Uint8Array(array_buffer)
	for (let i = 0; i < buffer.length; ++i) {
		view[i] = buffer[i]
	}
	return array_buffer
}

export async function write_cache_file({
	key,
	data,
	content_type,
	file_url
}: {
	key: string
	data: ArrayBufferLike
	content_type: string
	file_url: string
}): Promise<CachedItem> {
	const filename = encodeURIComponent(key)
	await fs.mkdir(CACHE_DIR, { recursive: true })

	const fullpath = path.join(CACHE_DIR, filename)

	await fs.writeFile(fullpath, Buffer.from(data))

	const item = {
		path: fullpath,
		timestamp: Date.now(),
		expires: Date.now() + CACHE_DURATION,
		original_url: file_url,
		content_type
	}

	FAVICON_CACHE.set(key, item)
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
			data: ArrayBuffer
			item: CachedItem
	  }
	| null
	| undefined
> {
	const cached = FAVICON_CACHE.get(key)
	console.log("checking favicon cache:", key, cached)
	if (cached && Date.now() < cached.expires) {
		if (cached.path) {
			try {
				const data = await fs.readFile(cached.path)
				return {
					data: to_array_buffer(data),
					item: cached
				}
			} catch {
				FAVICON_CACHE.delete(key)
			}
		}
	}

	if (cached === null) {
		return null
	}

	return undefined
}
