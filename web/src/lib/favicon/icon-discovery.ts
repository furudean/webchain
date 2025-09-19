import { parse } from "node-html-parser"
import type { HTMLElement } from "node-html-parser"
import { is_valid_url, safe_parse_url } from "$lib/url"

export async function get_icon_urls(
	base: URL | string,
	head: HTMLElement | null
): Promise<URL[]> {
	const selectors = ['link[rel="icon"]', 'link[rel="shortcut icon"]']
	const possible_icons: Set<URL> = new Set()

	if (head) {
		for (const selector of selectors) {
			const element = head.querySelector(selector)
			if (element?.hasAttribute("href")) {
				const href = element.getAttribute("href")!
				if (is_valid_url(href)) {
					possible_icons.add(new URL(href))
				} else {
					const parsed_url = safe_parse_url(href, base)
					if (parsed_url) {
						possible_icons.add(parsed_url)
					} else {
						console.log(`skipping invalid favicon url: ${href}`)
					}
				}
			}
		}
	}

	possible_icons.add(new URL("/favicon.ico", base))

	return Array.from(possible_icons.values())
}

export async function parse_page_for_icons(
	url: string,
	html: string
): Promise<URL[]> {
	const parsed = parse(html)
	if (!parsed) return []

	return get_icon_urls(url, parsed.querySelector("head"))
}
