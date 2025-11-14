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
const MAX_CONCURRENT_SNAPS = 10
const BROWSER_KEEPALIVE_MS = 120_000

let active_snap_count = 0

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
): Promise<{ data: Buffer; item: SnapSidecar } | null> {
	try {
		const metaPath = get_cache_path(url) + ".json"
		const imgPath = get_cache_path(url) + ".webp"
		const [metaRaw, imgRaw] = await Promise.all([
			fs.readFile(metaPath, "utf8"),
			fs.readFile(imgPath)
		])
		const sidecar: SnapSidecar = JSON.parse(metaRaw)
		if (Date.now() > sidecar.expires) return null
		return { data: imgRaw, item: sidecar }
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
	const item: SnapSidecar = {
		original_url: url,
		content_type: "image/webp",
		etag,
		expires: Date.now() + CACHE_DURATION_MS
	}
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

// Gracefully close browser on SIGINT
if (typeof process !== "undefined" && process.on) {
	process.on("SIGINT", async () => {
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
	browser: Browser
): Promise<Uint8Array<ArrayBufferLike>> {
	try {
		console.log("taking snap of", url_param)
		const page = await browser.newPage()
		await page.setExtraHTTPHeaders({
			"User-Agent": "WebchainSpider (+https://github.com/furudean/webchain)",
			"Accept-Language": "en-US,en;q=0.9,*;q=0.5"
		})

		const response = await page.goto(url_param, {
			waitUntil: "networkidle0",
			timeout: 30_000
		})

		if (!response || response.status() !== 200) {
			await page.close()
			throw new Error(
				`Failed to load page, status code: ${response ? response.status() : "unknown"}`
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
		console.error("Screenshot error for", url_param, err)
		throw new Error("Failed to take screenshot")
	}
}

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
}

async function make_snap_response({
	data,
	item,
	disk_cache,
	request,
	url_origin,
	not_modified = false
}: MakeSnapResponseParams): Promise<Response> {
	const headers = new Headers()
	headers.set("ETag", item.etag)
	headers.set("X-Original-URL", item.original_url)
	headers.set("Cache-Control", `public, max-age=${CACHE_DURATION_MS / 1000}`)
	headers.set("Expires", new Date(item.expires).toUTCString())
	headers.set("Access-Control-Allow-Origin", url_origin)
	headers.set("x-disk-cache", disk_cache)
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
		const { data, item } = cache_hit
		if (item.etag && if_none_match === item.etag) {
			return await make_snap_response({
				data: null,
				item,
				disk_cache: "HIT",
				request,
				url_origin: url.origin,
				not_modified: true
			})
		}
		return await make_snap_response({
			data,
			item,
			disk_cache: "HIT",
			request,
			url_origin: url.origin
		})
	}

	let fetch_promise = snap_fetch_promises.get(url_param)
	if (!fetch_promise) {
		if (active_snap_count >= MAX_CONCURRENT_SNAPS) {
			return text("too many concurrent screenshot requests", { status: 429 })
		}
		fetch_promise = (async () => {
			active_snap_count++
			try {
				const browser = await get_browser()
				const screenshot = await take_screenshot(url_param, browser)
				const item = await cache_snap(url_param, Buffer.from(screenshot))
				return { data: Buffer.from(screenshot), item }
			} catch (err) {
				console.error("Failed to fetch/capture screenshot for", url_param, err)
				throw text("Failed to capture screenshot", { status: 503 })
			} finally {
				active_snap_count--
				snap_fetch_promises.delete(url_param)
			}
		})()
		snap_fetch_promises.set(url_param, fetch_promise)
	}
	let fetch_result: { data: Buffer; item: SnapSidecar }
	try {
		fetch_result = await fetch_promise
	} catch (err) {
		if (snap_fetch_promises.get(url_param) === fetch_promise) {
			snap_fetch_promises.delete(url_param)
		}
		if (err instanceof Response) return err
		return text("Failed to capture screenshot", { status: 503 })
	}

	return await make_snap_response({
		data: fetch_result.data,
		item: fetch_result.item,
		disk_cache: "MISS",
		request,
		url_origin: url.origin
	})
}
