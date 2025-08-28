export interface Node {
	at: string
	children: string[]
	parent: string | null
	depth: number
	indexed: boolean,
	color: string,
}

