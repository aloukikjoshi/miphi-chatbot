# MiPhi Offline AI Assistant

A production-ready, offline AI chatbot for internal company use — powered by:

- **FastAPI** backend with JWT authentication
- **PostgreSQL** for user, session, and message persistence
- **vLLM** (GPU) for high-performance local LLM inference
- **LangChain RAG** with FAISS vector store and history-aware retrieval
- **Vanilla JS** frontend with SSE streaming chat
- **Meta Llama 3.2 1B Instruct** (bitsandbytes int8 quantization)
- **Docker Compose** for containerized services

This project demonstrates a secure, fully offline AI assistant architecture designed to run on your own hardware (Windows + WSL2 with NVIDIA GPU).

---

## Features

- **JWT Authentication** — Register/login with bcrypt hashed passwords
- **Persistent Chat History** — Full session and message storage in PostgreSQL
- **RAG (Retrieval-Augmented Generation)** — Context-aware answers from company documents
- **History-aware retrieval** — Understands multi-turn conversations
- **SSE Streaming** — Real-time token streaming to the browser
- **Structured Logging** — JSON logs with daily rotation and crash recovery markers
- **Health Monitoring** — Live vLLM status badge in the UI
- **Fully Offline** — No cloud APIs required after first model download
- **GPU-optimized** — bitsandbytes int8 quantization for GTX 1650 / 4GB VRAM class GPUs
- **CPU Fallback** — Slow but functional CPU-mode via separate Docker profile

---

## Architecture

```
Browser (Vanilla JS)
    |
    |  HTTP / SSE streaming
    v
FastAPI Backend (uvicorn :8080)
    |-- /api/auth/register   -- User registration
    |-- /api/auth/login      -- JWT token issuance
    |-- /api/chat/stream     -- SSE streaming chat endpoint
    |-- /api/chat/sessions   -- Session management
    |-- /api/health          -- vLLM + DB health check
    |
    |-- PostgreSQL (Docker :5432)
    |       |-- Users / ChatSessions / ChatMessages
    |
    |-- vLLM OpenAI-compatible API (Docker :8000)
            |-- Meta-Llama-3.2-1B-Instruct (bitsandbytes int8)
                    |-- FAISS vector store (company_context.txt)
```

---

## Project Structure

```
miphi-chatbot/
|
|-- backend/                        # FastAPI application
|   |-- __init__.py
|   |-- main.py                     # App entrypoint, routes, health check
|   |-- auth.py                     # JWT register/login endpoints
|   |-- chat.py                     # SSE streaming chat endpoint
|   |-- database.py                 # Async SQLAlchemy engine + session
|   |-- models.py                   # ORM: User, ChatSession, ChatMessage
|   |-- schemas.py                  # Pydantic request/response schemas
|   |-- middleware.py               # Request logging + CORS
|   |-- logger.py                   # JSON structured logger with rotation
|   |-- rag/
|       |-- retriever.py            # FAISS vector store builder
|       |-- llm_client.py           # LangChain RAG chain (history-aware)
|       |-- prompts.py              # System prompts
|
|-- frontend/                       # Vanilla JS + HTML UI
|   |-- index.html                  # Login / Register page
|   |-- chat.html                   # Chat page with streaming + health badge
|   |-- css/
|   |   |-- style.css               # Dark mode design system
|   |-- js/
|       |-- auth.js                 # Auth form logic
|       |-- chat.js                 # SSE streaming + health badge polling
|
|-- data/
|   |-- company_context.txt         # Company knowledge base for RAG
|
|-- logs/                           # Auto-created, gitignored
|   |-- miphi_YYYY-MM-DD.log        # Daily rotating JSON logs
|
|-- Dockerfile.backend              # Backend container image
|-- Dockerfile.chatbot              # Legacy Streamlit image (kept for reference)
|-- docker-compose.yml              # Services: postgres + vllm_gpu + vllm_cpu
|-- requirements.txt                # Python dependencies
|-- .env                            # Secrets (never commit)
|-- .gitignore
|-- .dockerignore
|-- run.sh                          # Quick launcher script
|
|  -- Legacy Streamlit files (kept for reference) --
|-- app.py
|-- llm_client.py
|-- prompts.py
|-- retriever.py
```

---

## System Requirements

### GPU Setup (Recommended)

| Component | Minimum |
|-----------|---------|
| OS | Windows 10/11 + WSL2 Ubuntu, or Linux |
| GPU | NVIDIA with CUDA (GTX 1650 / 4GB VRAM tested) |
| VRAM | 4 GB+ |
| RAM | 8 GB+ |
| Disk | 5 GB (model cache) |
| CUDA | 11.8 or higher |

### CPU Setup (Fallback — very slow)

| Component | Minimum |
|-----------|---------|
| OS | Windows 10/11 + WSL2 Ubuntu, or Linux |
| RAM | 16 GB+ |
| Disk | 5 GB (model cache) |

---

## Prerequisites

### 1. Install WSL2 + Ubuntu (Windows only)

```bash
wsl --install -d Ubuntu
```

### 2. Install Docker Desktop

Download from: https://www.docker.com/products/docker-desktop/

Enable in Docker Desktop settings:
- **Resources > WSL Integration > Ubuntu**
- **General > Use WSL 2 based engine**

Verify:

```bash
docker --version
docker compose version
```

### 3. NVIDIA GPU Drivers (GPU setup)

Install the latest NVIDIA drivers on Windows.

Verify GPU is visible in WSL:

```bash
nvidia-smi
```

---

## Setup & Installation

### 1. Clone the repository

```bash
git clone https://github.com/aloukikjoshi/miphi-chatbot.git
cd miphi-chatbot
```

### 2. Create Python virtual environment

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### 3. Configure environment variables

Create `.env` in the project root:

```env
# Model
APP_MODEL=meta-llama/Llama-3.2-1B-Instruct
APP_MAX_MODEL_LEN=2048
APP_GPU_MEM_UTIL=0.80

# vLLM
VLLM_BASE_URL=http://localhost:8000/v1
VLLM_MODEL=meta-llama/Llama-3.2-1B-Instruct

# PostgreSQL
DATABASE_URL=postgresql+asyncpg://miphi:miphi_secret@localhost:5432/miphi_db

# JWT Auth
JWT_SECRET_KEY=change-me-to-a-long-random-secret
JWT_EXPIRE_MINUTES=60

# Hugging Face token (required to download model)
HF_TOKEN=your_huggingface_token_here
```

**Never commit `.env` — it is gitignored.**

### 4. Add company context

Edit `data/company_context.txt` with your company's information.
This is the knowledge base the RAG pipeline retrieves from.

Tips:
- Keep it concise and factual
- Use technical descriptions of products/services
- Avoid confidential or sensitive data
- 1-5 pages of content works well

---

## Running the Application

### Step 1 — Start Docker services (GPU mode)

Run from **PowerShell on Windows** (Docker Desktop runs on Windows):

```powershell
docker compose up -d
```

This starts:
- **miphi-postgres** — PostgreSQL on port 5432
- **miphi-vllm-gpu** — vLLM with bitsandbytes int8 on port 8000

The vLLM container downloads the model on first run (~2.5 GB).
Wait until it is fully ready by watching logs:

```powershell
docker logs -f miphi-vllm-gpu
```

Look for: `Uvicorn running on http://0.0.0.0:8000`

### Step 2 — Start the FastAPI backend

Run from **WSL/Ubuntu terminal** inside the project:

```bash
source .venv/bin/activate
uvicorn backend.main:app --host 0.0.0.0 --port 8080 --reload
```

### Step 3 — Open the app

Navigate to:

```
http://localhost:8080
```

1. **Register** a new account on the login page
2. **Login** to access the chat interface
3. Start chatting with the assistant!

---

## CPU Fallback (No GPU)

To start vLLM in CPU-only mode (very slow — for testing only):

```powershell
docker compose --profile cpu up -d vllm_cpu
```

Then update `.env`:

```env
VLLM_BASE_URL=http://localhost:8001/v1
```

---

## API Reference

| Method | Endpoint | Auth Required | Description |
|--------|----------|---------------|-------------|
| POST | /api/auth/register | No | Register new user |
| POST | /api/auth/login | No | Login, receive JWT token |
| GET | /api/chat/sessions | JWT | List user chat sessions |
| POST | /api/chat/sessions | JWT | Create a new session |
| GET | /api/chat/stream | JWT | SSE streaming chat |
| GET | /api/health | No | vLLM + DB health status |
| GET | / | No | Serves the frontend UI |

---

## How RAG Works

The chatbot does **not** dump the full context document into every prompt. Instead:

1. `data/company_context.txt` is split into chunks and indexed with FAISS
2. On each user message, semantically similar chunks are retrieved
3. Only relevant chunks are injected into the prompt
4. The retriever is **history-aware** — it reformulates queries using past conversation turns
5. Full chat history is stored in PostgreSQL and passed as context

This prevents token overflow, hallucinated answers, and memory crashes.

---

## Logging

All requests and errors are logged to:

```
logs/miphi_YYYY-MM-DD.log
```

Log format is structured JSON for easy parsing and crash recovery:

```json
{
  "timestamp": "2026-06-11T18:30:00",
  "level": "INFO",
  "event": "chat_request",
  "user_id": 3,
  "session_id": "abc123",
  "latency_ms": 450
}
```

Logs rotate daily and are gitignored. Crash recovery markers are written on startup/shutdown.

---

## Troubleshooting

### vLLM container not starting

```powershell
docker logs miphi-vllm-gpu
```

Common causes:
- `HF_TOKEN` not set — add it to `.env`
- Model still downloading — wait a few minutes
- Out of VRAM — reduce `APP_GPU_MEM_UTIL` (e.g., `0.70`)
- NVIDIA drivers not installed on Windows

### PostgreSQL connection refused

```powershell
docker ps
docker logs miphi-postgres
```

Ensure `DATABASE_URL` in `.env` matches the compose service credentials.

### 500 errors on auth endpoints

Check FastAPI logs in the WSL terminal. Common causes:
- Database tables not yet created — run the backend once to auto-create them
- bcrypt version conflict — `requirements.txt` pins `bcrypt==4.0.1`

### JWT token rejected

- Token expires after `JWT_EXPIRE_MINUTES` minutes
- Ensure `JWT_SECRET_KEY` in `.env` is set and unchanged between restarts

### Model running slowly

The GTX 1650 (4GB VRAM) runs at ~8-15 tokens/second with int8 quantization.
To improve speed:
- Reduce `APP_MAX_MODEL_LEN` (e.g., `1024`)
- Reduce `--max-num-seqs` in `docker-compose.yml` (currently 4)

---

## Technologies Used

| Layer | Technology |
|-------|-----------|
| LLM Inference | vLLM (OpenAI-compatible API) |
| Model | Meta Llama 3.2 1B Instruct |
| Quantization | bitsandbytes int8 |
| Backend | FastAPI + Uvicorn |
| Database | PostgreSQL 16 + SQLAlchemy async |
| Auth | JWT (python-jose) + bcrypt |
| RAG | LangChain + FAISS + sentence-transformers |
| Frontend | Vanilla HTML / CSS / JavaScript |
| Streaming | Server-Sent Events (SSE) |
| Logging | Python logging + JSON + daily rotation |
| Containerization | Docker Compose |
| Platform | WSL2 Ubuntu + NVIDIA GPU |

---

## Security Notes

- Never commit `.env` — it contains `HF_TOKEN` and `JWT_SECRET_KEY`
- Use a strong, random `JWT_SECRET_KEY` in production
- The PostgreSQL password in `docker-compose.yml` is for local use only
- This project is designed for internal/intranet use, not public internet exposure
- Company context data should not include confidential or sensitive information

---

## Future Improvements

- Cloud PostgreSQL for cross-device session persistence
- Multi-user role management (admin / user)
- Larger quantized models (3B, 7B)
- AWQ 4-bit quantization for GPUs with compute capability >= 8.0
- Kubernetes deployment
- WebSocket support (in addition to SSE)
- Document upload UI for context management
- Multi-agent orchestration
