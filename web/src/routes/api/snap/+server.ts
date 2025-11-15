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
const CACHE_DURATION_MS = 60 * 60 * 24 * 1000 // 1 day in ms
const MAX_CONCURRENT_SNAPS = 5

// immediately preload cache on module load
initialize_cache_from_disk().catch((err) =>
	console.error("Failed to preload disk cache:", err)
)

// periodically clean up expired cache files every hour
if (typeof setInterval !== "undefined") {
	setInterval(
		() => {
			vacuum_cache().catch((err) =>
				console.error("Periodic cache cleanup error:", err)
			)
		},
		24 * 60 * 60 * 1000
	)
}

// close browser and abort requests on SIGINT
if (typeof process !== "undefined" && process.on) {
	process.on("SIGINT", async () => {
		for (const signal of abort_signals) {
			signal.abort()
		}
		if (browser) {
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

interface SnapSidecar {
	original_url: string
	content_type: string
	etag: string
	expires: number
}

function get_cache_path(url: string): string {
	const hash = createHash("sha256").update(url).digest("hex")
	return path.join(CACHE_DIR, hash)
}

async function get_cached_snap(
	url: string
): Promise<{ data: Buffer; sidecar: SnapSidecar; expired: boolean } | null> {
	try {
		const metaPath = get_cache_path(url) + ".json"
		const imgPath = get_cache_path(url) + ".webp"
		const [metaRaw, imgRaw] = await Promise.all([
			fs.readFile(metaPath, "utf8"),
			fs.readFile(imgPath)
		])
		const sidecar: SnapSidecar = JSON.parse(metaRaw)
		const expired = Date.now() > sidecar.expires
		return { data: imgRaw, sidecar: sidecar, expired }
	} catch {
		return null
	}
}

async function cache_snap(
	url: string,
	data: Buffer,
	abort_signal?: AbortSignal
): Promise<SnapSidecar> {
	if (abort_signal?.aborted) throw new Error("cache write aborted")
	await fs.mkdir(CACHE_DIR, { recursive: true })
	const etag = createHash("sha256")
		.update(new Uint8Array(data))
		.digest("hex")
		.slice(0, 16)
	const sidecar: SnapSidecar = {
		original_url: url,
		content_type: "image/webp",
		etag,
		expires: Date.now() + CACHE_DURATION_MS
	}
	if (abort_signal?.aborted) throw new Error("cache write aborted")
	await Promise.all([
		fs.writeFile(
			get_cache_path(url) + ".json",
			JSON.stringify(sidecar, null, "\t")
		),
		fs.writeFile(get_cache_path(url) + ".webp", data)
	])
	return sidecar
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

const abort_signals = new Set<AbortController>()
let browser: Browser | null = null
let browser_promise: Promise<Browser> | null = null

async function get_browser(): Promise<Browser> {
	if (browser) return browser
	if (browser_promise) return browser_promise

	console.log("launching persistent browser instance for snaps")
	browser_promise = puppeteer
		.launch({
			headless: true,
			args: ["--disable-features=FedCm"]
		})
		.then((launched_browser) => {
			browser = launched_browser
			browser_promise = null
			return browser
		})
		.catch((err) => {
			browser_promise = null
			throw err
		})
	return browser_promise
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
		await page.setCacheEnabled(false)
		await page.setViewport({
			width: 1024,
			height: 768
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
	Promise<{ data: Buffer; sidecar: SnapSidecar }>
>()

async function initialize_cache_from_disk() {
	try {
		await fs.mkdir(CACHE_DIR, { recursive: true })
		const files = await fs.readdir(CACHE_DIR)
		for (const file of files) {
			if (file.endsWith(".json")) {
				const meta_path = path.join(CACHE_DIR, file)
				const img_path = meta_path.replace(/\.json$/, ".webp")
				try {
					const meta = await fs.readFile(meta_path, "utf8")
					const sidecar: SnapSidecar = JSON.parse(meta)
					const data = await fs.readFile(img_path)
					// only preload non-expired cache
					if (Date.now() <= sidecar.expires) {
						snap_fetch_promises.set(
							sidecar.original_url,
							Promise.resolve({ data, sidecar })
						)
					}
				} catch {
					console.warn("corrupt snap cache entry:", meta_path)
					await fs.unlink(meta_path)
					await fs.unlink(img_path)
				}
			}
		}
		console.log(
			`loaded ${snap_fetch_promises.size} snap cache entries from disk`
		)
	} catch (err) {
		console.error("error preloading disk cache:", err)
	}
}

interface MakeSnapResponseParams {
	data: Buffer | null
	sidecar: SnapSidecar
	disk_cache: "HIT" | "MISS"
	request: Request
	url_origin: string
	not_modified?: boolean
	no_cache?: boolean
}

async function make_snap_response({
	data,
	sidecar,
	disk_cache,
	request,
	url_origin,
	not_modified = false,
	no_cache = false
}: MakeSnapResponseParams): Promise<Response> {
	const headers = new Headers()
	headers.set("ETag", `"${sidecar.etag}"`)
	headers.set("X-Original-URL", sidecar.original_url)
	headers.set("Access-Control-Allow-Origin", url_origin)
	headers.set("x-disk-cache", disk_cache)

	if (no_cache) {
		headers.set(
			"Cache-Control",
			"no-store, no-cache, must-revalidate, proxy-revalidate"
		)
		headers.set("Pragma", "no-cache")
		headers.set("Expires", "0")
	} else {
		headers.set(
			"Cache-Control",
			`public, max-age=${CACHE_DURATION_MS / 1000}, stale-while-revalidate=${CACHE_DURATION_MS / 1000}`
		)
		headers.set("Expires", new Date(sidecar.expires).toUTCString())
	}

	if (not_modified) {
		return new Response(null, { status: 304, headers })
	}
	headers.set("Content-Type", sidecar.content_type)
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

async function fetch_and_cache_snap(
	url_param: string,
	abort: AbortController
): Promise<{ data: Buffer; sidecar: SnapSidecar }> {
	const release = await snap_semaphore.acquire()
	try {
		const browser = await get_browser()
		const screenshot = await take_screenshot(url_param, browser, abort.signal)
		const sidecar = await cache_snap(
			url_param,
			Buffer.from(screenshot),
			abort.signal
		)
		return { data: Buffer.from(screenshot), sidecar }
	} finally {
		release()
		abort_signals.delete(abort)
		snap_fetch_promises.delete(url_param)
	}
}

export const GET: RequestHandler = async ({ url, request, fetch }) => {
	const url_param = url.searchParams.get("url")
	const force_refresh = url.searchParams.has("refresh")

	if (!url_param) {
		return text("url parameter required", { status: 400 })
	}

	if (!is_valid_url(url_param)) {
		return text("invalid url parameter", { status: 400 })
	}

	if (!(await get_allowed_fetch_urls(fetch))) {
		return text("nice try, but i thought about that", { status: 400 })
	}

	if (!force_refresh) {
		const cache_hit = await get_cached_snap(url_param)
		const if_none_match = request.headers.get("if-none-match")

		if (cache_hit) {
			const { data, sidecar, expired } = cache_hit
			if (sidecar.etag && if_none_match === sidecar.etag && !expired) {
				return await make_snap_response({
					data: null,
					sidecar,
					disk_cache: "HIT",
					request,
					url_origin: url.origin,
					not_modified: true
				})
			}
			if (!expired) {
				return await make_snap_response({
					data,
					sidecar,
					disk_cache: "HIT",
					request,
					url_origin: url.origin
				})
			}
			// serve stale cache, trigger background refresh if not already running
			let refresh_promise = snap_fetch_promises.get(url_param)
			if (!refresh_promise) {
				const abort = new AbortController()
				abort_signals.add(abort)
				refresh_promise = fetch_and_cache_snap(url_param, abort).catch(
					(err) => {
						if (abort.signal.aborted) {
							console.error("Refresh aborted for", url_param)
							throw err
						}
						console.error("failed to refresh screenshot for", url_param, err)
						throw err
					}
				)
				snap_fetch_promises.set(url_param, refresh_promise)
			}
			return await make_snap_response({
				data,
				sidecar,
				disk_cache: "HIT",
				request,
				url_origin: url.origin
			})
		}
	}

	let fetch_promise = snap_fetch_promises.get(url_param)
	if (!fetch_promise) {
		if (snap_semaphore.count === 0) {
			return text("too many concurrent requests", { status: 429 })
		}
		const abort = new AbortController()
		abort_signals.add(abort)
		fetch_promise = fetch_and_cache_snap(url_param, abort).catch((err) => {
			if (abort.signal.aborted) {
				throw text("request aborted by server", { status: 503 })
			}
			console.error("Failed to fetch/capture screenshot for", url_param, err)
			throw text("failed to capture screenshot", { status: 503 })
		})
		snap_fetch_promises.set(url_param, fetch_promise)
	}
	let fetch_result: { data: Buffer; sidecar: SnapSidecar }
	try {
		fetch_result = await fetch_promise
	} catch (err) {
		if (err instanceof Response) return err
		return text("failed to capture screenshot", { status: 503 })
	}

	return await make_snap_response({
		data: fetch_result.data,
		sidecar: fetch_result.sidecar,
		disk_cache: "MISS",
		request,
		url_origin: url.origin,
		no_cache: force_refresh
	})
}

async function vacuum_cache() {
	try {
		await fs.mkdir(CACHE_DIR, { recursive: true })
		const files = await fs.readdir(CACHE_DIR)
		for (const file of files) {
			if (file.endsWith(".json")) {
				const metaPath = path.join(CACHE_DIR, file)
				try {
					const metaRaw = await fs.readFile(metaPath, "utf8")
					const sidecar: SnapSidecar = JSON.parse(metaRaw)
					if (Date.now() > sidecar.expires) {
						// Remove both .json and .webp
						await Promise.all([
							fs.unlink(metaPath),
							fs.unlink(metaPath.replace(/\.json$/, ".webp")).catch(() => {})
						])
					}
				} catch {
					// if corrupt, remove meta file
					await fs.unlink(metaPath)
				}
			}
		}
	} catch (err) {
		console.error("error cleaning up cache:", err)
	}
}
