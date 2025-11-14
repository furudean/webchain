import puppeteer from "puppeteer"
import type { Browser } from "puppeteer"
import type { RequestHandler } from "./$types"
import { is_valid_url } from "$lib/url"
import { text } from "@sveltejs/kit"
import { promises as fs } from "fs"
import path from "path"
import { createHash } from "node:crypto"
import { compress_if_accepted } from "$lib/compress"
import { get_allowed_fetch_urls } from "$lib/crawler"

const CACHE_DIR = path.resolve(process.cwd(), ".snap-cache")
const CACHE_DURATION_MS = 60 * 60 * 24 * 3 * 1000 // 3 days in ms
const MAX_CONCURRENT_SNAPS = 5
const BROWSER_KEEPALIVE_MS = 120_000

interface SnapSidecar {
	original_url: string
	content_type: string
	etag: string
	expires: number
}

function get_cache_path(url: string): string {
	// Use SHA256 hash for safe, fixed-length filenames
	const hash = createHash("sha256").update(url).digest("hex")
	return path.join(CACHE_DIR, hash)
}

async function get_cached_snap(
	url: string
): Promise<{ data: Buffer; item: SnapSidecar; expired: boolean } | null> {
	try {
		const metaPath = get_cache_path(url) + ".json"
		const imgPath = get_cache_path(url) + ".webp"
		const [metaRaw, imgRaw] = await Promise.all([
			fs.readFile(metaPath, "utf8"),
			fs.readFile(imgPath)
		])
		const sidecar: SnapSidecar = JSON.parse(metaRaw)
		const expired = Date.now() > sidecar.expires
		return { data: imgRaw, item: sidecar, expired }
	} catch {
		return null
	}
}

async function cache_snap(
	url: string,
	data: Buffer,
	abortSignal?: AbortSignal
): Promise<SnapSidecar> {
	if (abortSignal?.aborted) throw new Error("Cache write aborted")
	await fs.mkdir(CACHE_DIR, { recursive: true })
	const etag = createHash("sha256")
		.update(new Uint8Array(data))
		.digest("hex")
		.slice(0, 16)
	const item: SnapSidecar = {
		original_url: url,
		content_type: "image/webp",
		etag,
		expires: Date.now() + CACHE_DURATION_MS
	}
	if (abortSignal?.aborted) throw new Error("Cache write aborted")
	await Promise.all([
		fs.writeFile(
			get_cache_path(url) + ".json",
			JSON.stringify(item, null, "\t")
		),
		fs.writeFile(get_cache_path(url) + ".webp", data)
	])
	return item
}

export const OPTIONS: RequestHandler = async ({ url }) => {
	const headers = new Headers()
	headers.set("Access-Control-Allow-Origin", url.origin)
	headers.set("Access-Control-Allow-Methods", "*")
	headers.set("Access-Control-Allow-Headers", "*")
	return new Response(null, {
		status: 204,
		headers
	})
}

let browser: Browser | null = null
let browser_close_timer: NodeJS.Timeout | null = null

// Track active abort controllers for requests
const abortcontrollers = new Set<AbortController>()

// Gracefully close browser and abort requests on SIGINT
if (typeof process !== "undefined" && process.on) {
	process.on("SIGINT", async () => {
		console.log("sigint: aborting active screenshot requests")
		for (const controller of abortcontrollers) {
			controller.abort()
		}
		if (browser) {
			console.log("sigint: closing browser instance")
			try {
				await browser.close()
			} catch (err) {
				console.error("error closing browser on SIGINT:", err)
				process.exit(1)
			}
			browser = null
		}
		process.exit(0)
	})
}

async function get_browser(): Promise<Browser> {
	function reset_browser_close_timer() {
		if (browser_close_timer) clearTimeout(browser_close_timer)
		browser_close_timer = setTimeout(() => {
			console.log("closing idle browser instance")
			browser?.close().catch((err) => {
				console.error("error closing browser:", err)
				browser = null
			})
		}, BROWSER_KEEPALIVE_MS)
	}

	if (browser) {
		reset_browser_close_timer()
		return browser
	}
	console.log("launching new browser instance for snaps")
	browser = await puppeteer.launch({
		headless: true,
		args: ["--disable-features=FedCm"] // idk but prevents crashes
	})
	reset_browser_close_timer()
	return browser
}

async function take_screenshot(
	url_param: string,
	browser: Browser,
	abortSignal?: AbortSignal
): Promise<Uint8Array<ArrayBufferLike>> {
	const page = await browser.newPage()
	try {
		console.log("taking snap of", url_param)
		await page.setExtraHTTPHeaders({
			"User-Agent": "WebchainSpider (+https://github.com/furudean/webchain)",
			"Accept-Language": "en-US,en;q=0.9,*;q=0.5"
		})

		if (abortSignal) {
			abortSignal.addEventListener("abort", () => {
				page.close().catch(() => {})
			})
		}

		const response = await page.goto(url_param, {
			waitUntil: "networkidle0",
			timeout: 30_000
		})

		if (!response?.ok()) {
			await page.close()
			throw new Error(
				`failed to load page, status code: ${response ? response.status() : "unknown"}`
			)
		}

		const screenshot = await page.screenshot({
			encoding: "binary",
			type: "webp"
		})
		await page.close()
		console.log("done snap of", url_param)
		return screenshot
	} catch (err) {
		await page.close().catch(() => {})
		if (abortSignal?.aborted) {
			console.error("Screenshot aborted for", url_param)
			throw new Error("Screenshot aborted")
		}
		console.error("screenshot error for", url_param, err)
		throw new Error("failed to take screenshot")
	}
}

class Semaphore {
	private tasks: (() => void)[] = []
	public count: number
	constructor(max: number) {
		this.count = max
	}
	async acquire(): Promise<() => void> {
		return new Promise((resolve) => {
			const try_acquire = () => {
				if (this.count > 0) {
					this.count--
					resolve(() => {
						this.count++
						if (this.tasks.length) {
							const next = this.tasks.shift()
							if (next) next()
						}
					})
				} else {
					this.tasks.push(try_acquire)
				}
			}
			try_acquire()
		})
	}
}

const snap_semaphore = new Semaphore(MAX_CONCURRENT_SNAPS)

const snap_fetch_promises = new Map<
	string,
	Promise<{ data: Buffer; item: SnapSidecar }>
>()

interface MakeSnapResponseParams {
	data: Buffer | null
	item: SnapSidecar
	disk_cache: "HIT" | "MISS"
	request: Request
	url_origin: string
	not_modified?: boolean
	stale?: boolean
}

async function make_snap_response({
	data,
	item,
	disk_cache,
	request,
	url_origin,
	not_modified = false,
	stale = false
}: MakeSnapResponseParams): Promise<Response> {
	const headers = new Headers()
	headers.set("ETag", item.etag)
	headers.set("X-Original-URL", item.original_url)
	headers.set(
		"Cache-Control",
		`public, max-age=${CACHE_DURATION_MS / 1000}, stale-while-revalidate=${CACHE_DURATION_MS / 1000}`
	)
	headers.set("Expires", new Date(item.expires).toUTCString())
	headers.set("Access-Control-Allow-Origin", url_origin)
	headers.set("x-disk-cache", disk_cache)
	if (stale) headers.set("Warning", '110 - "Response is stale"')
	if (not_modified) {
		return new Response(null, { status: 304, headers })
	}
	headers.set("Content-Type", item.content_type)
	if (data) {
		const { body, encoding } = await compress_if_accepted(data, request)
		if (encoding) headers.set("Content-Encoding", encoding)
		return new Response(
			Buffer.from(body instanceof ArrayBuffer ? new Uint8Array(body) : body),
			{ headers }
		)
	}
	return new Response(null, { status: 500, headers })
}

export const GET: RequestHandler = async ({ url, request, fetch }) => {
	const url_param = url.searchParams.get("url")

	if (!url_param) {
		return text("url parameter required", { status: 400 })
	}

	if (!is_valid_url(url_param)) {
		return text("invalid url parameter", { status: 400 })
	}

	if (!(await get_allowed_fetch_urls(fetch))) {
		return text("nice try, but i thought about that", { status: 400 })
	}

	const cache_hit = await get_cached_snap(url_param)
	const if_none_match = request.headers.get("if-none-match")

	if (cache_hit) {
		const { data, item, expired } = cache_hit
		if (item.etag && if_none_match === item.etag && !expired) {
			return await make_snap_response({
				data: null,
				item,
				disk_cache: "HIT",
				request,
				url_origin: url.origin,
				not_modified: true
			})
		}
		if (!expired) {
			return await make_snap_response({
				data,
				item,
				disk_cache: "HIT",
				request,
				url_origin: url.origin
			})
		}
		// Serve stale cache, trigger background refresh if not already running
		let refresh_promise = snap_fetch_promises.get(url_param)
		if (!refresh_promise) {
			const abort = new AbortController()
			abortcontrollers.add(abort)
			refresh_promise = (async () => {
				const release = await snap_semaphore.acquire()
				try {
					const browser = await get_browser()
					const screenshot = await take_screenshot(
						url_param,
						browser,
						abort.signal
					)
					const item = await cache_snap(
						url_param,
						Buffer.from(screenshot),
						abort.signal
					)
					return { data: Buffer.from(screenshot), item }
				} catch (err) {
					if (abort.signal.aborted) {
						console.error("Refresh aborted for", url_param)
						throw err
					}
					console.error("failed to refresh screenshot for", url_param, err)
					throw err
				} finally {
					release()
					abortcontrollers.delete(abort)
					snap_fetch_promises.delete(url_param)
				}
			})()
			snap_fetch_promises.set(url_param, refresh_promise)
		}
		return await make_snap_response({
			data,
			item,
			disk_cache: "HIT",
			request,
			url_origin: url.origin,
			stale: true
		})
	}

	let fetch_promise = snap_fetch_promises.get(url_param)
	if (!fetch_promise) {
		if (snap_semaphore.count === 0) {
			return text("too many concurrent screenshot requests", { status: 429 })
		}
		const abort = new AbortController()
		abortcontrollers.add(abort)
		fetch_promise = (async () => {
			const release = await snap_semaphore.acquire()
			try {
				const browser = await get_browser()
				const screenshot = await take_screenshot(
					url_param,
					browser,
					abort.signal
				)
				const item = await cache_snap(
					url_param,
					Buffer.from(screenshot),
					abort.signal
				)
				return { data: Buffer.from(screenshot), item }
			} catch (err) {
				if (abort.signal.aborted) {
					console.error("Request aborted for", url_param)
					throw text("Request aborted", { status: 503 })
				}
				console.error("Failed to fetch/capture screenshot for", url_param, err)
				throw text("Failed to capture screenshot", { status: 503 })
			} finally {
				release()
				abortcontrollers.delete(abort)
				snap_fetch_promises.delete(url_param)
			}
		})()
		snap_fetch_promises.set(url_param, fetch_promise)
	}
	let fetch_result: { data: Buffer; item: SnapSidecar }
	try {
		fetch_result = await fetch_promise
	} catch (err) {
		if (err instanceof Response) return err
		return text("failed to capture screenshot", { status: 503 })
	}

	return await make_snap_response({
		data: fetch_result.data,
		item: fetch_result.item,
		disk_cache: "MISS",
		request,
		url_origin: url.origin
	})
}
