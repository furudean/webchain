import type { CrawlResponse } from "./node"

const REFRESH_INTERVAL = 5 * 60_000 // 5 minutes

let allowed_favicon_urls: Set<string> | null = null
let last_fetch = 0
let current_fetch: Promise<Response> | null = null

export async function get_allowed_favicon_urls(
	fetch_fn: typeof fetch
): Promise<Set<string>> {
	const now = Date.now()
	if (allowed_favicon_urls && now - last_fetch < REFRESH_INTERVAL) {
		return allowed_favicon_urls
	}
	try {
		const request = current_fetch ?? fetch_fn("/crawler/current.json")
		const response = await request
		current_fetch = null
		if (!response.ok)
			throw new Error(`failed to fetch crawler data: ${response.status}`)
		const crawl: Partial<CrawlResponse> = await response.json()
		const ats = crawl.nodes?.map((node) => node.at)
		if (!ats) throw new Error("No nodes in crawl response")
		allowed_favicon_urls = new Set(ats)
		last_fetch = now
		return allowed_favicon_urls
	} catch (err) {
		console.error("failed to refresh allowed favicon URLs", err)
		throw err
	}
}
