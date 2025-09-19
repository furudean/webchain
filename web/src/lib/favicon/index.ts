export interface CachedItem {
	path?: string
	timestamp: number
	expires: number
	content_type?: string
	original_url?: string
	etag?: string
}

export const FAVICON_CACHE_DURATION = 60 * 60 * 1000 // 1 hour
export const EMPTY_FAVICON_CACHE_DURATION = 10 * 60 * 1000 // 10 minutes
export const STALE_THRESHOLD = 60 * 60 * 1000 // 1 hour stale window

export {
	is_stale_but_valid,
	write_cache_file,
	get_cached_file,
	cache_empty_favicon
} from "./storage"

export {
	fetch_and_cache_favicon,
	refresh_favicon_in_background
} from "./favicon-fetcher"
