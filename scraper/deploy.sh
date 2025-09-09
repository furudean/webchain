#!/usr/bin/env bash

set -euxo pipefail
cd "$(dirname "$0")"

uv build

scp dist/webchain_scraper-0.0.0-py3-none-any.whl webchain.milkmedicine.net:/root

ssh webchain.milkmedicine.net "
	uv tool install webchain_scraper-0.0.0-py3-none-any.whl --force && \
	/root/crawl.sh
"
