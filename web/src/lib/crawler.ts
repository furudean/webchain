import type { CrawledNode, CrawlResponse } from "./node"

const REFRESH_INTERVAL = 5 * 60_000 // 5 minutes

let current_crawl: CrawledNode[] | undefined = undefined
let last_fetch = 0
let ongoing_fetch: Promise<Partial<CrawlResponse> | undefined> | null = null

export async function get_current_crawl(
	fetch_fn: typeof fetch
): Promise<typeof current_crawl> {
	const now = Date.now()
	if (current_crawl && now - last_fetch < REFRESH_INTERVAL) {
		return current_crawl
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

		current_crawl = crawl?.nodes
		last_fetch = now
		return current_crawl
	} catch (err) {
		console.error("failed to refresh allowed favicon URLs", err)
		throw err
	}
}

export async function is_webchain_node(url: string, fetch_fn: typeof fetch) {
	const crawl = await get_current_crawl(fetch_fn)
	if (!crawl) throw new Error("no crawl data available")
	return crawl.find((node) => node.at === url) !== undefined
}

/**
 * best effort check whether we are allowed to crawl the given URL based on the current crawl data
 */
export async function robots_ok(at: string, fetch_fn: typeof fetch) {
	const crawl = await get_current_crawl(fetch_fn)
	if (!crawl) return true
	const current_node = crawl.find((node) => node.at === at)

	return current_node?.robots_ok !== false
}
