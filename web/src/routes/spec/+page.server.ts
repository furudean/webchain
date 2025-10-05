import MarkdownIt from "markdown-it"
import footnote from "markdown-it-footnote"
import anchor from "markdown-it-anchor"
import toc from "markdown-it-table-of-contents"
import type { PageServerLoad } from "../$types"
import spec from "../../../../SPEC.md?raw"

const md = MarkdownIt({
	html: true,
	typographer: true
})
	.use(footnote)
	.use(anchor)
	.use(toc)

export const load: PageServerLoad = async () => {
	return {
		html: md.render(spec)
	}
}
