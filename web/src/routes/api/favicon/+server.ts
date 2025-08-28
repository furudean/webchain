import { json } from "@sveltejs/kit"
import type { RequestHandler } from "./$types"

const CACHE_DURATION = 60 * 60 * 1000
const FAVICON_CACHE = new Map<string, { data: ArrayBuffer | undefined; timestamp: number }>()

export const GET: RequestHandler = async ({ url }) => {
	const url_param = url.searchParams.get("url")

	if (!url_param) {
		return json({ error: "url parameter required" }, { status: 400 })
	}

	try {
		// First, follow the URL to get the final domain after redirects
		const url_response = await fetch(url_param, {
			method: 'HEAD',
			redirect: 'follow'
		})

		const followed_url = url_response.url
		const domain = new URL(followed_url).hostname

		// Check if favicon is already cached and not expired
		const now = Date.now()

		if (FAVICON_CACHE.has(domain)) {
			const cached = FAVICON_CACHE.get(domain)!

			// Check if cache entry is expired
			if (now - cached.timestamp > CACHE_DURATION) {
				FAVICON_CACHE.delete(domain)
			} else {
				// Cache hit and not expired
				if (cached.data === undefined) {
					// Favicon was previously not found, return no content
					return new Response(null, { status: 204 })
				}
				return new Response(cached.data, {
					status: 200,
					headers: {
						"Content-Type": "image/x-icon",
						"Cache-Control": "public, max-age=3600",
						"Content-Length": cached.data.byteLength.toString()
					}
				})
			}
		}

		const faviconUrl = `https://icons.duckduckgo.com/ip3/${domain}.ico`
		const response = await fetch(faviconUrl)

		if (!response.ok) {
			// Cache the fact that favicon wasn't found
			FAVICON_CACHE.set(domain, { data: undefined, timestamp: now })
			return new Response(null, { status: 204 })
		}

		const arrayBuffer = await response.arrayBuffer()

		// Cache the favicon
		FAVICON_CACHE.set(domain, { data: arrayBuffer, timestamp: now })

		return new Response(arrayBuffer, {
			status: 200,
			headers: {
				"Content-Type": response.headers.get("content-type") || "image/x-icon",
				"Cache-Control": "public, max-age=3600",
				"Content-Length": arrayBuffer.byteLength.toString()
			}
		})
	} catch (error) {
		console.error("error fetching favicon:", error)
		return json({ error: "failed to fetch favicon" }, { status: 500 })
	}
}
