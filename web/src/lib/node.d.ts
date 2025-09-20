export interface HtmlMetadata {
	title: string | null
	description: string | null
	theme_color: string | null
}

export interface CrawledNode {
	at: string
	children: string[]
	parent: string | null
	depth: number
	indexed: boolean
	html_metadata: HtmlMetadata | null
}

export interface Node extends CrawledNode {
	url: URL
	generated_color: string
	label: string
	url_param: string
}
