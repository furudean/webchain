#!/usr/bin/env bash

set -e
cd "$(dirname "$0")"

npm run build

rsync -zhave ssh --progress build webchain.milkmedicine.net:/var/www/
ssh webchain.milkmedicine.net "
    cd /var/www/ && \
    rm -rf webchain.milkmedicine.net && \
    mv build webchain.milkmedicine.net && \
    chown -R node:node webchain.milkmedicine.net && \
    systemctl restart node.service
"
