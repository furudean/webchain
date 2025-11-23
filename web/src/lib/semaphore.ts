export class Semaphore {
	private tasks: (() => void)[] = []
	public free: number
	constructor(max: number) {
		this.free = max
	}
	async acquire(): Promise<() => void> {
		return new Promise((resolve) => {
			const try_acquire = () => {
				if (this.free > 0) {
					this.free--
					resolve(() => {
						this.free++
						if (this.tasks.length) {
							const next = this.tasks.shift()
							if (next) next()
						}
					})
				} else {
					this.tasks.push(try_acquire)
				}
			}
			try_acquire()
		})
	}
}
