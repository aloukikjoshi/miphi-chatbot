#!/usr/bin/env bash
set -e

# Load app env vars
set -a
source .env
set +a

if command -v nvidia-smi >/dev/null 2>&1; then
    echo "GPU detected."
    export APP_RUNTIME=gpu
else
    echo "No GPU detected."
    export APP_RUNTIME=cpu
fi

bash scripts/start_vllm.sh