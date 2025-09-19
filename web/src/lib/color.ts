import { oklab_to_rgb } from "oklab.ts"

/**
 * @param x 0..255
 */
function to_hex(x: number): string {
	return Math.round(x).toString(16).padStart(2, "0")
}

function hash_string(str: string): number {
	let hash = 5381
	for (let i = 0; i < str.length; i++) {
		hash = (hash << 5) + hash + str.charCodeAt(i) // hash * 33 + c
	}
	return Math.abs(hash) // 0..2^31 - 1
}

export function string_to_color(
	string: string,
	saturation: number = 0.2, // 0..1
	lightness: number = 0.7 // 0..1
): string {
	const good_hues = [15, 45, 75, 135, 195, 225, 285, 315] // warmer, more pleasant hues
	const hash = hash_string(string) // 0..2^31 - 1
	// use hue to rotate around the color wheel
	const selected_hue = good_hues[hash % good_hues.length] // 0..360
	const hue = selected_hue / 360 // 0..1
	const angle = hue * 2 * Math.PI // 0..2π
	const ok = {
		L: lightness, // 0..1
		a: Math.cos(angle) * saturation, // 0..1
		b: Math.sin(angle) * saturation // 0..1
	}

	// convert oklab to rgb
	const { r, g, b } = oklab_to_rgb(ok)

	const hex = `#${to_hex(r)}${to_hex(g)}${to_hex(b)}`

	return hex
}
