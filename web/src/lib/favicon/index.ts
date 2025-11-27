export interface CachedItem {
	path?: string
	timestamp: number
	expires: number
	stale_after?: number
	content_type?: string
	original_url?: string
	etag?: string
}

export const FAVICON_CACHE_DURATION_MS = 7 * 24 * 60 * 60 * 1000 // 7 days
export const EMPTY_FAVICON_CACHE_DURATION_MS = 30 * 60 * 1000 // 30 minutes
export const STALE_THRESHOLD_MS = 24 * 60 * 60 * 1000 // 24 hours

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
