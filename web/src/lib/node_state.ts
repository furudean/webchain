import type GraphType from "graphology"
import { writable } from "svelte/store"

export const highlighted_node = writable<string | undefined>(undefined)
export const hovered_node = writable<string | undefined>(undefined)
export const current_graph = writable<GraphType>(undefined)

export function clear_highlighted(graph: GraphType): void {
	for (const node of graph.nodes()) {
		graph.setNodeAttribute(node, "highlighted", false)
	}
}

export function set_highlighted_node(node: string | undefined) {
	highlighted_node.set(node)
}

export function set_hovered_node(node: string | undefined) {
	hovered_node.set(node)
}

export function set_graph(graph: GraphType) {
	current_graph.set(graph)
}
