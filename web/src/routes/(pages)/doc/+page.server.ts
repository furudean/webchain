import type { PageServerLoad } from "./$types"
import { entries } from "./[slug]/+page.server"

export const load: PageServerLoad = async () => {
	const routes = await entries()
	return {
		routes
	}
}
