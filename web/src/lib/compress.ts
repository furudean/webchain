import { gzipSync, deflateSync } from "node:zlib"

export async function compress_if_accepted(
	data: Uint8Array | Buffer | ArrayBuffer,
	request: Request
): Promise<{ body: Uint8Array | Buffer | ArrayBuffer; encoding?: string }> {
	const acceptEncoding = request.headers.get("accept-encoding") || ""
	if (/\bgzip\b/.test(acceptEncoding)) {
		return {
			body: gzipSync(data),
			encoding: "gzip"
		}
	}
	if (/\bdeflate\b/.test(acceptEncoding)) {
		return {
			body: deflateSync(data),
			encoding: "deflate"
		}
	}
	return { body: data, encoding: undefined }
}
