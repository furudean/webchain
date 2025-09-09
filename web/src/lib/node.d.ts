export interface HtmlMetadata {
	title: string | null
	description: string | null
	color: string | null
}

export interface CrawledNode {
	hash: string
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
}
