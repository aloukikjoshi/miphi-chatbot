# README.md

# MiPhi Offline AI Assistant

An offline AI chatbot powered by:
- vLLM
- Streamlit
- Meta Llama 3.2 1B Instruct
- Dynamic context retrieval
- CPU/GPU adaptive deployment
- Dockerized frontend architecture

This project demonstrates a production-style local AI assistant architecture capable of running on both CPU-only and GPU-enabled systems.

---

# Features

- Offline AI inference
- Local vLLM serving
- Dynamic CPU/GPU backend detection
- Dockerized chatbot UI
- Streaming responses
- Dynamic context retrieval
- Lightweight RAG-style architecture
- OpenAI-compatible backend API
- Works with Windows + WSL2
- Works on Linux systems
- Works with NVIDIA GPU or CPU-only environments

---

# Architecture

```text
Host Machine
    └── vLLM Backend
            ├── GPU Runtime (if NVIDIA GPU available)
            └── CPU Runtime (fallback)

Docker Container
    └── Streamlit Chatbot UI
```

The chatbot container communicates with the local vLLM backend through:

```text
http://host.docker.internal:8000/v1
```

---

# Project Structure

```text
miphi-chatbot/
│
├── app.py
├── llm_client.py
├── prompts.py
├── context_loader.py
├── retriever.py
├── requirements.txt
├── .env
│
├── Dockerfile.chatbot
├── docker-compose.yml
│
├── scripts/
│   ├── bootstrap.sh
│   └── start_vllm.sh
│
├── data/
│   └── company_context.txt
│
├── .dockerignore
├── .gitignore
│
└── README.md
```

---

# System Requirements

## Minimum CPU System

- Windows 10/11 or Linux
- WSL2 Ubuntu recommended on Windows
- Python 3.11+
- Docker Desktop
- 16 GB RAM recommended
- Internet required only for first model download

## Recommended GPU System

- NVIDIA GPU
- CUDA-supported drivers
- 4 GB+ VRAM
- Docker Desktop
- WSL2 Ubuntu

---

# Required Software

## 1. Install WSL2 Ubuntu

Install Ubuntu through Microsoft Store.

Verify:

```bash
wsl
```

---

## 2. Install Python

Inside Ubuntu:

```bash
sudo apt update
sudo apt install -y python3 python3-pip python3-venv
```

Verify:

```bash
python3 --version
```

---

## 3. Install Docker Desktop

Install Docker Desktop:

https://www.docker.com/products/docker-desktop/

Enable:
- WSL Integration
- Ubuntu integration

Verify:

```bash
docker --version
```

---

# Clone Repository

```bash
git clone https://github.com/YOUR_USERNAME/miphi-chatbot.git

cd miphi-chatbot
```

---

# Configure Environment Variables

Create:

```text
.env
```

Add:

```env
APP_RUNTIME=auto

APP_MODEL=meta-llama/Llama-3.2-1B-Instruct

APP_CPU_ENV=/home/inno/vllm-env
APP_GPU_ENV=/home/inno/vllm-env

APP_MAX_MODEL_LEN=4096

APP_GPU_MEM_UTIL=0.75

VLLM_CPU_KVCACHE_SPACE=4

VLLM_BASE_URL=http://host.docker.internal:8000/v1
```

Update environment paths according to your machine.

---

# Install dos2unix

Required for fixing Linux shell script formatting.

```bash
sudo apt update
sudo apt install -y dos2unix
```

Run:

```bash
dos2unix .env scripts/*.sh
```

---

# Create vLLM Environment

## CPU Environment

```bash
python3 -m venv ~/vllm-env

source ~/vllm-env/bin/activate

pip install vllm
```

---

## GPU Environment

Install CUDA-enabled PyTorch and vLLM.

Example:

```bash
python3 -m venv ~/vllm-env

source ~/vllm-env/bin/activate

pip install torch --index-url https://download.pytorch.org/whl/cu121

pip install vllm
```

Verify GPU:

```bash
nvidia-smi
```

---

# Hugging Face Access

The model requires Hugging Face access.

## Create account

https://huggingface.co/

## Login

```bash
huggingface-cli login
```

Enter your Hugging Face token.

Recommended token permission:
- Read access

---

# Start vLLM Backend

Inside project directory:

```bash
bash scripts/bootstrap.sh
```

The system automatically:
- detects GPU
- otherwise falls back to CPU
- launches correct vLLM runtime

Successful startup should show:

```text
Uvicorn running on http://0.0.0.0:8000
```

---

# Start Docker Chatbot

In another terminal:

```bash
docker compose up --build
```

---

# Open Chatbot

Open browser:

```text
http://localhost:8501
```

---

# How Context Retrieval Works

The chatbot does NOT inject the full company document into the prompt.

Instead:

1. The context file is split into chunks.
2. Relevant chunks are dynamically retrieved.
3. Only relevant information is injected.
4. Prompt budget is preserved.

This prevents:
- token overflow
- irrelevant answers
- memory crashes
- hallucinations

---

# Supported Modes

## CPU Mode

Activated automatically when:

```text
No NVIDIA GPU detected
```

Uses:
- CPU inference
- reduced KV cache
- lower memory usage

---

## GPU Mode

Activated automatically when:

```text
NVIDIA GPU detected
```

Uses:
- CUDA acceleration
- GPU KV cache
- faster inference

---

# Troubleshooting

## 1. Invalid model repo id

Fix:

```bash
dos2unix .env scripts/*.sh
```

---

## 2. Docker build context too large

Ensure `.dockerignore` exists.

Example:

```text
.venv
__pycache__
.env
.git
```

---

## 3. Token overflow errors

Reduce:

```env
APP_MAX_MODEL_LEN
```

or shorten:
- company_context.txt
- chat history

---

## 4. GPU not detected

Verify:

```bash
nvidia-smi
```

If unavailable:
- reinstall NVIDIA drivers
- enable WSL GPU support

---

## 5. vLLM backend not reachable

Ensure:

```bash
bash scripts/bootstrap.sh
```

is running.

---

# Updating Company Context

Edit:

```text
data/company_context.txt
```

Recommended:
- concise information
- technical descriptions
- product details
- public company information only

Avoid:
- confidential information
- huge raw dumps
- irrelevant text

---

# Security Notes

- Never expose private company data.
- Never commit `.env` files.
- Never publish Hugging Face tokens.
- This project is intended for educational and demonstration purposes.

---

# Future Improvements

Possible upgrades:

- Vector database integration
- Embedding retrieval
- Multi-model routing
- User authentication
- Persistent chat memory
- Remote inference servers
- Kubernetes deployment
- Quantized model support
- Multi-agent orchestration

---

# Technologies Used

- Python
- Streamlit
- vLLM
- Docker
- Hugging Face Transformers
- OpenAI-compatible APIs
- Meta Llama 3.2 1B Instruct

---

