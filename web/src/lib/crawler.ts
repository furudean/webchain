import type { CrawlResponse } from "./node"

const REFRESH_INTERVAL = 5 * 60_000 // 5 minutes

let allowed_fetch_urls: Set<string> | null = null
let last_fetch = 0
let ongoing_fetch: Promise<Partial<CrawlResponse> | undefined> | null = null

export async function get_webchain_urls(
	fetch_fn: typeof fetch
): Promise<Set<string>> {
	const now = Date.now()
	if (allowed_fetch_urls && now - last_fetch < REFRESH_INTERVAL) {
		return allowed_fetch_urls
	}
	try {
		// merge incoming request if another is ongoing
		const request =
			ongoing_fetch ??
			fetch_fn("/crawler/current.json").then((response) => {
				if (!response.ok)
					throw new Error(`failed to fetch crawler data: ${response.status}`)
				return response.json() as Promise<Partial<CrawlResponse>>
			})
		ongoing_fetch = request
		const crawl = await request
		ongoing_fetch = null

		const ats = crawl?.nodes?.map((node) => node.at)
		if (!ats) throw new Error("no nodes in crawl response")
		allowed_fetch_urls = new Set(ats)
		last_fetch = now
		return allowed_fetch_urls
	} catch (err) {
		console.error("failed to refresh allowed favicon URLs", err)
		throw err
	}
}
