export interface CrawledNode {
	at: string
	children: string[]
	parent: string | null
	depth: number
	indexed: boolean
	color: string
}

export interface Node extends CrawledNode {
	url: URL
	color: string
	label: string
}
