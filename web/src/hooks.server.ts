import { CACHE_DIR } from "$lib/cache"
import fs from "node:fs/promises"

async function init() {
	await fs.rm(CACHE_DIR, { recursive: true, force: true })
	await fs.mkdir(CACHE_DIR, { recursive: true })
}

init().catch((e) => console.error("Failed to initialize favicon cache", e))
