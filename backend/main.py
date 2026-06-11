import sys, os
import httpx
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from backend.database import engine, Base
from backend.middleware import RequestLoggingMiddleware, setup_cors
from backend.auth import router as auth_router
from backend.chat import router as chat_router
from backend.logger import log_startup, log_crash, get_logger
from dotenv import load_dotenv

load_dotenv()
logger = get_logger("miphi.main")
VLLM_BASE_URL = os.getenv("VLLM_BASE_URL", "http://localhost:8000/v1")
VLLM_MODEL = os.getenv("VLLM_MODEL", "meta-llama/Llama-3.2-1B-Instruct")

@asynccontextmanager
async def lifespan(app: FastAPI):
    try:
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        logger.info("DB tables ready", extra={"user_id": None, "session_id": None, "latency_ms": None, "status_code": None})
        from backend.rag.retriever import get_retriever
        from backend.rag.llm_client import get_rag_chain
        get_retriever()
        get_rag_chain()
        logger.info("RAG chain ready", extra={"user_id": None, "session_id": None, "latency_ms": None, "status_code": None})
        log_startup()
    except Exception as exc:
        log_crash(exc)
        sys.exit(1)
    yield
    logger.info("SHUTDOWN", extra={"event": "SHUTDOWN", "user_id": None, "session_id": None, "latency_ms": None, "status_code": None})

app = FastAPI(title="MiPhi AI Assistant API", version="2.0.0", lifespan=lifespan)
setup_cors(app)
app.add_middleware(RequestLoggingMiddleware)
app.include_router(auth_router)
app.include_router(chat_router)

@app.get("/api/health")
async def health_check():
    """Check if backend and vLLM are reachable."""
    vllm_ok = False
    vllm_models = []
    try:
        async with httpx.AsyncClient(timeout=3.0) as client:
            r = await client.get(f"{VLLM_BASE_URL.rstrip('/v1')}/v1/models")
            if r.status_code == 200:
                vllm_ok = True
                data = r.json()
                vllm_models = [m["id"] for m in data.get("data", [])]
    except Exception as e:
        logger.warning("vLLM health check failed: %s", str(e), extra={"user_id": None, "session_id": None, "latency_ms": None, "status_code": None})

    return JSONResponse({
        "status": "ok",
        "vllm": {
            "reachable": vllm_ok,
            "url": VLLM_BASE_URL,
            "model": VLLM_MODEL,
            "loaded_models": vllm_models,
        }
    })

app.mount("/", StaticFiles(directory="frontend", html=True), name="frontend")
