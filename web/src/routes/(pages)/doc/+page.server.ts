import type { PageServerLoad } from "./$types"
import { entries } from "./[slug]/+page.server"

export const prerender = true

export const load: PageServerLoad = async () => {
	const routes = await entries()
	return {
		routes
	}
}
