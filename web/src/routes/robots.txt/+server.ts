import type { RequestHandler } from "./$types"

export const prerender = true

export const GET: RequestHandler = async () => {
	const file = await fetch(
		"https://api.github.com/repos/ai-robots-txt/ai.robots.txt/releases/latest"
	)

	if (!file.ok) throw new Error("failed to fetch robots.txt release info")

	const release = await file.json()
	const asset = release?.assets?.find(
		(asset: Record<string, unknown>) => asset.name === "robots.txt"
	)
	if (!asset) throw new Error("robots.txt asset not found in release")

	const robots_fetch = await fetch(asset.browser_download_url)
	const text = await robots_fetch.text()

	return new Response(text, {
		status: 200,
		headers: {
			"Content-Type": "text/plain",
			"Cache-Control": "public, max-age=86400"
		}
	})
}
