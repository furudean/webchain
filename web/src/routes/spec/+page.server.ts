import MarkdownIt from "markdown-it"
import footnote from "markdown-it-footnote"
import anchor from "markdown-it-anchor"
import type { PageServerLoad } from "../$types"
import spec from "../../../../SPEC.md?raw"

export const prerender = true

const md = MarkdownIt({
	html: true,
	typographer: true
})
	.use(footnote)
	.use(anchor)

export const load: PageServerLoad = async () => {
	return {
		html: md.render(spec)
	}
}
