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
import env_paths from "env-paths"
import { dev } from "$app/environment"

const paths = env_paths("webchain-web-server")

const CACHE_DIR = path.join(dev ? process.cwd() : paths.cache, ".snap-cache")
const CACHE_DURATION_MS = 60 * 60 * 24 * 1000 // 1 day in ms
const MAX_CONCURRENT_SNAPS = 3

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

async function cache_snap(url: string, data: Buffer): Promise<SnapSidecar> {
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

let browser: Browser | null = null
let browser_promise: Promise<Browser> | null = null

const existing_sigint_handlers = process.listeners("SIGTERM")
process.on("SIGTERM", async (signal) => {
	if (browser) {
		try {
			const pages = await browser.pages()
			for (const page of pages) {
				await page.close()
			}
			await browser.close()
			console.log("Closed browser and all pages on SIGINT")
		} catch (err) {
			console.error("Error closing browser/pages on SIGINT:", err)
		}
	}
	for (const listener of existing_sigint_handlers) {
		listener(signal)
	}
})

async function get_browser(): Promise<Browser> {
	if (browser) return browser
	if (browser_promise) return browser_promise

	console.log("launching persistent browser instance for snaps")
	browser_promise = puppeteer
		.launch({
			headless: true,
			userDataDir: ".chrome",
			args: [
				"--no-sandbox", // Disables Chrome's security sandbox
				"--no-zygote", // Disables zygote (chrome process for faster startup) process
				"--disable-setuid-sandbox", // Disables setuid sandbox (often used with --no-sandbox)
				"--disable-gpu", // Disables GPU hardware acceleration
				"--disable-software-rasterizer", // Reduces CPU usage for rendering
				"--disable-background-timer-throttling", // Prevents Chrome from slowing down timers in background tabs
				"--disable-backgrounding-occluded-windows", // Keeps occluded windows active
				"--disable-renderer-backgrounding", // Prevents renderer processes from backgrounding

				"--disable-extensions", // Disables browser extensions
				"--disable-default-apps", // Prevents loading of default Chrome apps
				"--disable-component-extensions-with-background-pages", // Disables component extensions with background pages
				"--disable-background-networking", // Disables background network requests
				"--disable-sync", // Disables Google Account syncing

				"--disable-breakpad" // Disables crash reporting
			],
			handleSIGTERM: false
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
	browser: Browser
): Promise<Uint8Array<ArrayBufferLike>> {
	const context = await browser.createBrowserContext()
	const page = await context.newPage()
	page.setDefaultNavigationTimeout(30000)
	page.setDefaultTimeout(30000)

	try {
		console.log("taking snap of", url_param)
		await page.setExtraHTTPHeaders({
			"User-Agent": "WebchainSpider (+https://github.com/furudean/webchain)",
			"Accept-Language": "en-US,en;q=0.9,*;q=0.5"
		})
		await page.setViewport({
			width: 1024,
			height: 768
		})

		const response = await page.goto(url_param, {
			waitUntil: "networkidle2",
			timeout: 30_000
		})

		if (!response?.ok()) {
			await page.close()
			throw new Error(
				`failed to load page, status code: ${response ? response.status() : "unknown"}`
			)
		}

		const screenshot = await Promise.race([
			page.screenshot({
				encoding: "binary",
				type: "webp"
			}),
			new Promise<never>((_, reject) =>
				setTimeout(() => reject(new Error("screenshot timed out")), 15_000)
			)
		])

		await page.close()
		console.log("done snap of", url_param)
		return screenshot
	} catch (err) {
		console.error("screenshot error for", url_param, err)
		await page.close().catch(() => {})
		throw new Error("failed to take screenshot")
	} finally {
		await context.close()
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

interface MakeSnapResponseParams {
	data: Buffer | null
	sidecar: SnapSidecar
	disk_cache: "HIT" | "MISS"
	request: Request
	url_origin: string
	not_modified?: boolean
	no_cache?: boolean
	stale?: boolean
}

async function make_snap_response({
	data,
	sidecar,
	disk_cache,
	request,
	url_origin,
	not_modified = false,
	no_cache = false,
	stale = false
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
	} else if (stale) {
		headers.set(
			"Cache-Control",
			`public, max-age=0, must-revalidate, stale-while-revalidate=${CACHE_DURATION_MS / 1000}`
		)
		headers.set("Expires", new Date(sidecar.expires).toUTCString())
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
	url_param: string
): Promise<{ data: Buffer; sidecar: SnapSidecar }> {
	const release = await snap_semaphore.acquire()
	try {
		const browser = await get_browser()
		const screenshot = await take_screenshot(url_param, browser)
		const sidecar = await cache_snap(url_param, Buffer.from(screenshot))
		return { data: Buffer.from(screenshot), sidecar }
	} finally {
		release()
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
				refresh_promise = fetch_and_cache_snap(url_param).catch((err) => {
					console.error("failed to refresh screenshot for", url_param, err)
					throw err
				})
				snap_fetch_promises.set(url_param, refresh_promise)
			}
			return await make_snap_response({
				data,
				sidecar,
				disk_cache: "HIT",
				request,
				url_origin: url.origin,
				stale: true
			})
		}
	}

	let fetch_promise = snap_fetch_promises.get(url_param)
	if (!fetch_promise) {
		if (snap_semaphore.count === 0) {
			return text("too many concurrent requests", { status: 429 })
		}
		fetch_promise = fetch_and_cache_snap(url_param).catch((err) => {
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
