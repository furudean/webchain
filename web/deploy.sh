#!/usr/bin/env bash

set -euxo pipefail
cd "$(dirname "$0")"

HOST=webchain.milkmedicine.net
DESTINATION="/home/node/webchain.milkmedicine.net"
SERVICE_NAME="webchain-site.service"

npm run build

rsync -zhave ssh --progress build "$HOST:/home/node/"

ssh $HOST "
    systemctl stop $SERVICE_NAME && \
    rm -rf $DESTINATION && \
    mv /home/node/build $DESTINATION && \
    chown -R node:node $DESTINATION && \
    systemctl start $SERVICE_NAME
"
