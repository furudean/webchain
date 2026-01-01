import node_adapter from "@sveltejs/adapter-node"
import { vitePreprocess } from "@sveltejs/vite-plugin-svelte"

/** @type {import('@sveltejs/kit').Config} */
const config = {
	// Consult https://svelte.dev/docs/kit/integrations
	// for more information about preprocessors
	preprocess: vitePreprocess(),

	compilerOptions: {
		runes: true
	},

	kit: {
		// See https://svelte.dev/docs/kit/adapters for more information about adapters.
		adapter: node_adapter(),

		alias: {
			"$doc/*": "../doc/*"
		}
	}
}

export default config
