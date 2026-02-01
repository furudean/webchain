import tr46 from "tr46"

export function is_valid_url(str: string): boolean {
	let url: URL | undefined

	try {
		url = new URL(str)
	} catch {
		return false
	}

	return url.protocol === "http:" || url.protocol === "https:"
}

export function safe_parse_url(href: string, base: string | URL): URL | null {
	try {
		return new URL(href, base)
	} catch {
		return null
	}
}

export function nice_url(url: string | URL): string {
	url = new URL(url)

	return tr46.toUnicode(url.hostname.replace(/^www\./i, "")).domain +
		url.pathname.replace(/\/$/, "")
}
