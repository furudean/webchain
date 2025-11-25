import { promises as fs } from "fs"
import path from "path"
import { createHash } from "node:crypto"
import type { Browser } from "puppeteer"
import puppeteer from "puppeteer"
import { dev } from "$app/environment"
import env_paths from "env-paths"
import { Semaphore } from "./semaphore"

const paths = env_paths("webchain-web-server")
export const CACHE_DIR = path.join(
	// use current working directory for cache in dev mode, else use OS tmp
	dev ? process.cwd() : paths.cache,
	".snap-cache"
)

export const CACHE_DURATION_MS = 60 * 60 * 24 * 1000 // 1 day in ms
export const MAX_CONCURRENT_SNAPS = 3

const in_flight_snaps = new Map<
	string,
	Promise<{ data: Buffer; sidecar: SnapSidecar }>
>()

export interface SnapSidecar {
	url: string
	sidecar_path: string
	image_path: string
	content_type: string
	etag: string
	expires: number
}

function disk_cache_location_for_snap(url: string): string {
	const hash = createHash("sha256").update(url).digest("hex")
	return path.join(CACHE_DIR, hash)
}

export async function get_cached_snap(
	url: string
): Promise<{ data: Buffer; sidecar: SnapSidecar; expired: boolean } | null> {
	try {
		const sidecar_path = disk_cache_location_for_snap(url) + ".json"
		const img_path = disk_cache_location_for_snap(url) + ".webp"
		const [meta_raw, img_raw] = await Promise.all([
			fs.readFile(sidecar_path, "utf8"),
			fs.readFile(img_path)
		])
		const sidecar: SnapSidecar = JSON.parse(meta_raw)
		const expired = Date.now() > sidecar.expires
		return { data: img_raw, sidecar, expired }
	} catch {
		return null
	}
}

async function cache_snap(
	url: string,
	data: Buffer,
	CACHE_DIR: string
): Promise<SnapSidecar> {
	await fs.mkdir(CACHE_DIR, { recursive: true })
	const etag = createHash("sha256")
		.update(new Uint8Array(data))
		.digest("hex")
		.slice(0, 16)
	const disk_cache_path = disk_cache_location_for_snap(url)
	const image_path = disk_cache_path + ".webp"
	const sidecar_path = disk_cache_path + ".json"
	const sidecar: SnapSidecar = {
		url,
		content_type: "image/webp",
		sidecar_path,
		image_path,
		etag,
		expires: Date.now() + CACHE_DURATION_MS
	}
	await Promise.all([
		fs.writeFile(image_path, data),
		fs.writeFile(sidecar_path, JSON.stringify(sidecar, null, "\t"))
	])
	return sidecar
}

async function read_cache_index(): Promise<SnapSidecar[]> {
	const snaps: SnapSidecar[] = []

	const files = await fs.readdir(CACHE_DIR)

	for (const file of files) {
		if (file.endsWith(".json")) {
			const sidecar_path = path.join(CACHE_DIR, file)
			const sidecar_file = await fs.readFile(sidecar_path, "utf8")
			const sidecar: SnapSidecar = JSON.parse(sidecar_file)
			snaps.push(sidecar)
		}
	}

	return snaps
}

export async function vacuum_cache() {
	try {
		const index = await read_cache_index()
		for (const sidecar of index) {
			if (Date.now() > sidecar.expires) {
				console.log("removing expired snap cache for", sidecar.url)
				await Promise.all([
					fs.unlink(sidecar.sidecar_path),
					fs.unlink(sidecar.image_path)
				])
			}
		}
	} catch (err) {
		console.error("error cleaning up cache:", err)
	}
}

let browser: Browser | null = null
let browser_promise: Promise<Browser> | null = null

async function get_browser(): Promise<Browser> {
	if (browser) return browser
	if (browser_promise) return browser_promise

	console.log("launching persistent browser instance for snaps")

	try {
		browser_promise = puppeteer.launch({
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
			handleSIGTERM: false // we override with our own handler
		})
	} catch (err) {
		console.error("failed to launch browser for snaps:", err)
		throw err
	}

	browser = await browser_promise

	browser.on("disconnected", () => {
		console.warn("browser disconnected")
		browser = null
		browser_promise = null
	})

	return browser
}

async function take_screenshot(
	url_param: string,
	browser: Browser
): Promise<Uint8Array<ArrayBufferLike>> {
	const context = await browser.createBrowserContext()
	const page = await context.newPage()
	page.setDefaultNavigationTimeout(30000)
	page.setDefaultTimeout(30000)

	console.log("taking snapshot for", url_param)

	try {
		await page.setExtraHTTPHeaders({
			"User-Agent": "WebchainSpider (+https://github.com/furudean/webchain)",
			"Accept-Language": "en-US,en;q=0.9,*;q=0.5"
		})
		await page.setViewport({
			width: 1024,
			height: 768
		})

		const response = await page.goto(url_param, {
			waitUntil: "networkidle0",
			timeout: 30_000
		})

		if (!response?.ok()) {
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

		return screenshot
	} finally {
		context.close().catch(() => {
			console.error("oh no!!! failed to close browser context")
		})
	}
}

const snap_semaphore = new Semaphore(MAX_CONCURRENT_SNAPS)

/**
 * fetches a screenshot for the given URL, deduplicating any requests for the same URL in flight
 * and caching the result on disk
 */
export async function atomic_fetch_and_cache_snap(
	url_param: string
): Promise<{ data: Buffer; sidecar: SnapSidecar }> {
	async function get() {
		const browser = await get_browser()
		const screenshot = await take_screenshot(url_param, browser)
		const buffer = Buffer.from(screenshot)
		const sidecar = await cache_snap(url_param, buffer, CACHE_DIR)
		return { data: buffer, sidecar }
	}

	if (in_flight_snaps.has(url_param)) {
		return in_flight_snaps.get(url_param)!
	}

	const release = await snap_semaphore.acquire()
	const promise = get()
	in_flight_snaps.set(url_param, promise)

	try {
		return await promise
	} finally {
		release()
		in_flight_snaps.delete(url_param)
	}
}

export async function fetch_and_cache_outdated_snaps(): Promise<void> {
	const index = await read_cache_index()
	const expired = index.filter((snap) => Date.now() > snap.expires)
	console.log(
		`found ${expired.length}/${index.length} expired snaps to refetch`
	)

	if (expired.length === 0) return

	const results = await Promise.allSettled(
		expired.map((snap) => atomic_fetch_and_cache_snap(snap.url))
	)

	const ok = results.filter((r) => r.status === "fulfilled").length
	console.log(`refetched ${ok}/${expired.length} expired snaps`)
}
