import fs from "node:fs/promises"

export async function safe_read_file(filepath: string): Promise<string | null> {
	try {
		return await fs.readFile(filepath, "utf-8")
	} catch {
		return null
	}
}

export async function safe_read_buffer(
	filepath: string
): Promise<Buffer | null> {
	try {
		return await fs.readFile(filepath)
	} catch {
		return null
	}
}

export async function safe_unlink(filepath: string): Promise<void> {
	try {
		await fs.unlink(filepath)
	} catch {
		// ignore errors
	}
}

export async function safe_access(filepath: string): Promise<boolean> {
	try {
		await fs.access(filepath)
		return true
	} catch {
		return false
	}
}
