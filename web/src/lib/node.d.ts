export interface HtmlMetadata {
	title: string | null
	description: string | null
}

export interface CrawledNode {
	hash: string
	at: string
	children: string[]
	parent: string | null
	depth: number
	indexed: boolean
	color: string
	html_metadata: HtmlMetadata | null
}

export interface Node extends CrawledNode {
	url: URL
	color: string
	label: string
}
