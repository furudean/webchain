#!/usr/bin/env bash

set -euxo pipefail
cd "$(dirname "$0")"

HOST=webchain.milkmedicine.net
DESTINATION="/root"

uv build

scp dist/webchain_spider-0.0.0-py3-none-any.whl $HOST:$DESTINATION

ssh $HOST "
    /root/.local/bin/uv tool install webchain_spider-0.0.0-py3-none-any.whl --force && \
    rm webchain_spider-0.0.0-py3-none-any.whl && \
    /root/crawl.sh
"
