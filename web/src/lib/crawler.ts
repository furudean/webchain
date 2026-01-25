import type { CrawlResponse } from "./node"

const REFRESH_INTERVAL = 60_000 // 1 minute

let current_crawl: CrawlResponse | undefined = undefined
let last_etag: string | null = null
let last_fetch = 0
let ongoing_fetch: Promise<CrawlResponse | undefined> | null = null

async function get_current_crawl(
	fetch_fn: typeof fetch
): Promise<CrawlResponse> {
	const now = Date.now()
	if (current_crawl && now - last_fetch < REFRESH_INTERVAL) {
		return current_crawl
	}

	try {
		const headers = new Headers()
		if (last_etag) headers.append('if-none-match', last_etag)

		// merge incoming request if another is ongoing
		const request =
			ongoing_fetch ??
			fetch_fn("/crawler/current.json", {
				headers,
			}).then((response) => {
				if (response.ok) {
					last_etag = response.headers.get('etag')
					return response.json() as Promise<CrawlResponse>
				}

				if (response.status === 304 && current_crawl)
					return current_crawl

				throw new Error(`failed to fetch crawler data: ${response.status}`)
			})
		ongoing_fetch = request
		current_crawl = await request
		ongoing_fetch = null

		last_fetch = now
		return current_crawl!
	} catch (err) {
		console.error("failed to refresh allowed favicon URLs", err)
		throw err
	}
}

export async function is_webchain_node(url: string, fetch_fn: typeof fetch) {
	const crawl = await get_current_crawl(fetch_fn)
	if (!crawl) throw new Error("no crawl data available")
	return crawl.nodes.find((node) => node.at === url) !== undefined
}

/**
 * best effort check whether we are allowed to crawl the given URL based on the current crawl data
 */
export async function robots_ok(at: string, fetch_fn: typeof fetch) {
	const crawl = await get_current_crawl(fetch_fn)
	if (!crawl) return true
	const current_node = crawl.nodes.find((node) => node.at === at)

	return current_node?.robots_ok !== false
}
