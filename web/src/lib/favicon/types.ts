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
