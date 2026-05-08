#!/usr/bin/env bash

set -e

# Load app env vars
set -a
source .env
set +a

MODEL_NAME="${APP_MODEL:-meta-llama/Llama-3.2-1B-Instruct}"
RUNTIME="${APP_RUNTIME:-auto}"
MAX_LEN="${APP_MAX_MODEL_LEN:-2048}"

echo "Selected runtime: ${RUNTIME}"
echo "Using model: ${MODEL_NAME}"
echo "Using max model len: ${MAX_LEN}"

if [ "$RUNTIME" = "cpu" ]; then

    export VLLM_CPU_KVCACHE_SPACE="${VLLM_CPU_KVCACHE_SPACE:-4}"

    CPU_ENV="${APP_CPU_ENV}"

    echo "Using CPU environment: ${CPU_ENV}"

    if [ ! -f "${CPU_ENV}/bin/activate" ]; then
        echo "CPU environment not found."
        exit 1
    fi

    source "${CPU_ENV}/bin/activate"

    exec vllm serve "$MODEL_NAME" \
        --dtype bfloat16 \
        --max-model-len "${MAX_LEN}" \
        --enforce-eager

else

    export VLLM_MEMORY_PROFILER_ESTIMATE_CUDAGRAPHS=0

    GPU_ENV="${APP_GPU_ENV}"

    echo "Using GPU environment: ${GPU_ENV}"

    if [ ! -f "${GPU_ENV}/bin/activate" ]; then
        echo "GPU environment not found."
        exit 1
    fi

    source "${GPU_ENV}/bin/activate"

    exec vllm serve "$MODEL_NAME" \
        --dtype half \
        --max-model-len "${MAX_LEN}" \
        --gpu-memory-utilization "${APP_GPU_MEM_UTIL:-0.75}" \
        --enforce-eager
fi