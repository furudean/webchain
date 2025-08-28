import fs from "node:fs/promises"
import path from "node:path"

fs.rm(path.resolve(".favicon_cache"), { recursive: true, force: true }).catch(() => {})
