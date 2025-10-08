export interface HtmlMetadata {
	title: string | null
	description: string | null
	theme_color: string | null
}

export interface CrawledNode {
	at: string
	children: string[]
	unqualified: string[]
	parent: string | null
	depth: number
	indexed: boolean
	first_seen: string | null
	last_updated: string | null
	html_metadata: HtmlMetadata | null
}

export interface DisplayNode extends CrawledNode {
	index: number
	url: URL
	generated_color: string
	label: string
	url_param: string
	first_seen: Date | null
	last_updated: Date | null
}
