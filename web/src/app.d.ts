// See https://svelte.dev/docs/kit/types#app.d.ts
// for information about these interfaces
declare global {
	namespace App {
		// interface Error {}
		// interface Locals {}
		// interface PageData {}
		interface PageState {
			node?: string
		}
		// interface Platform {}
	}

	declare module "*?arraybuffer" {
		const value: ArrayBuffer
		export default value
	}
}

export {}
