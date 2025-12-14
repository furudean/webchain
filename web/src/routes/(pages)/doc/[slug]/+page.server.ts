import MarkdownIt from "markdown-it"
import footnote from "markdown-it-footnote"
import anchor from "markdown-it-anchor"
import frontmatter_plugin from "markdown-it-front-matter"
import type { PageServerLoad, EntryGenerator } from "./$types"
import { error } from "@sveltejs/kit"
import { basename } from "node:path"
import frontmatter from "front-matter"

interface FrontMatter {
	title?: string
}

const md = MarkdownIt({
	html: true,
	typographer: true
})
	.use(footnote)
	.use(anchor)
	.use(frontmatter_plugin, () => {})

const pages = Object.fromEntries(
	Object.entries(
		import.meta.glob("$doc/*.md", { query: "?raw", import: "default" })
	).map(([key, value]) => [basename(key), value])
) as Record<string, (() => Promise<string>) | undefined>

export const entries: EntryGenerator = () => {
	return Object.keys(pages).map((slug) => ({ slug }))
}

export const load: PageServerLoad = async ({ params }) => {
	const page = pages[params.slug]

	if (!page) {
		return error(404, "Page not found")
	}

	const markdown = await page()

	return {
		html: md.render(markdown),
		frontmatter: frontmatter<FrontMatter>(markdown).attributes
	}
}
