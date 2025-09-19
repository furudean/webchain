export type { CachedItem } from "./types"
export {
	FAVICON_CACHE_DURATION,
	EMPTY_FAVICON_CACHE_DURATION,
	STALE_THRESHOLD
} from "./types"

export {
	is_stale_but_valid,
	cleanup_expired_cache,
	write_cache_file,
	get_cached_file,
	cache_empty_favicon
} from "./storage"

export { is_valid_url } from "./icon-discovery"

export {
	fetch_and_cache_favicon,
	refresh_favicon_in_background
} from "./favicon-fetcher"
