import { oklab_to_rgb } from "oklab.ts"

function to_hex(x: number) {
	return Math.round(x).toString(16).padStart(2, "0")
}

function hash_string(str: string): number {
	let hash = 5381
	for (let i = 0; i < str.length; i++) {
		hash = ((hash << 5) + hash) + str.charCodeAt(i) // hash * 33 + c
	}
	return Math.abs(hash)
}

export function string_to_color(
	string: string,
	saturation: number = 0.2, // 0..1
	lightness: number = 0.6 // 0..1
): string {
	const hash = hash_string(string)

	// use hue to rotate around the color wheel
	const hue = ((hash % 360) / 360) // 0..1
	const angle = hue * 2 * Math.PI
	const ok = {
		L: lightness,
		a: Math.cos(angle) * saturation,
		b: Math.sin(angle) * saturation
	}

	console.log(ok)

	// Convert oklab to rgb
	const { r, g, b } = oklab_to_rgb(ok)

	console.log({r, g, b})

	const hex = `#${to_hex(r)}${to_hex(g)}${to_hex(b)}`
	console.log(hex)

	return hex
}
