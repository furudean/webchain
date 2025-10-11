export const date_fmt = new Intl.DateTimeFormat("en-US", {
	year: "numeric",
	month: "short",
	day: "numeric"
})

export const date_time_fmt = new Intl.DateTimeFormat("en-US", {
	year: "numeric",
	month: "short",
	day: "numeric",
	hour: "2-digit",
	minute: "2-digit"
})
