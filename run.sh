#!/usr/bin/env bash

set -e

if docker run --rm --gpus all \
    nvidia/cuda:12.1.0-base-ubuntu22.04 \
    nvidia-smi >/dev/null 2>&1
then
    echo "GPU runtime detected."

    export COMPOSE_PROFILES=gpu

else
    echo "CPU mode."

    export COMPOSE_PROFILES=cpu
fi

docker compose pull

docker compose up