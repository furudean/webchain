#!/usr/bin/env bash

set -euxo pipefail
cd "$(dirname "$0")"

# we use docker to build the application with the right environment and then
# copy it back. in a better world this would simply be `npm run build`.
#
# we do this because of the dependency node-html-parser, which creates a build
# that can't run on our target linux box (debian)
#
# docker build --platform=linux/amd64 --output=. .
npm run build

rsync -zhave ssh --progress build webchain.milkmedicine.net:/var/www/

ssh webchain.milkmedicine.net "
    cd /var/www/ && \
	systemctl stop node.service && \
    rm -rf webchain.milkmedicine.net && \
    mv build webchain.milkmedicine.net && \
    chown -R node:node webchain.milkmedicine.net && \
    systemctl start node.service
"
