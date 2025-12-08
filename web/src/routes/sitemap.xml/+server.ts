import { html } from "common-tags"
import type { RequestHandler } from "./$types"
import { entries as doc_entries } from "../doc/[slug]/+page.server"

const static_routes = Object.keys(
	import.meta.glob("/src/routes/**/+page.svelte")
)
	.filter((route) => !route.includes("[slug]"))
	.map((page) => page.replace("/src/routes", "").replace("+page.svelte", ""))

function create_url_element(
	url: URL,
	lastmod: Date | undefined = undefined
): string {
	return html`
		<url>
			<loc>${url.href}</loc>
			${lastmod
				? "<lastmod>" + lastmod.toISOString().slice(0, 10) + "</lastmod>"
				: ""}
		</url>
	`
}

export const GET: RequestHandler = async ({ url }) => {
	const documents = await doc_entries()

	const url_elements = [
		...static_routes.map((route) =>
			create_url_element(new URL(route, url.protocol + url.host))
		),
		...documents.map((doc) =>
			create_url_element(new URL(`/doc/${doc.slug}`, url.protocol + url.host))
		)
	]

	const xml = html`
		<?xml version="1.0" encoding="UTF-8" ?>
		<urlset xmlns="https://www.sitemaps.org/schemas/sitemap/0.9">
			${url_elements.join("\n")}
		</urlset>
	`

	return new Response(xml, {
		headers: {
			"Content-Type": "application/xml"
		}
	})
}
