import time, uuid
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import StreamingResponse
from langchain_core.messages import HumanMessage, AIMessage
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession
from backend.auth import verify_token
from backend.database import get_db, AsyncSessionLocal
from backend.models import User, ChatSession, ChatMessage, MessageRole
from backend.rag.llm_client import get_rag_chain
from backend.schemas import SessionCreate, SessionOut, MessageOut, ChatRequest
from backend.logger import get_logger

logger = get_logger("miphi.chat")
router = APIRouter(prefix="/api/chat", tags=["chat"])

@router.post("/sessions", response_model=SessionOut, status_code=201)
async def create_session(payload: SessionCreate, current_user: User = Depends(verify_token), db: AsyncSession = Depends(get_db)):
    session = ChatSession(user_id=current_user.id, title=payload.title or "New Chat")
    db.add(session); await db.flush()
    logger.info("Session created", extra={"user_id": str(current_user.id), "session_id": str(session.id), "latency_ms": None, "status_code": 201})
    return session

@router.get("/sessions", response_model=list[SessionOut])
async def list_sessions(current_user: User = Depends(verify_token), db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(ChatSession).where(ChatSession.user_id == current_user.id).order_by(ChatSession.updated_at.desc()))
    return result.scalars().all()

@router.get("/sessions/{session_id}/messages", response_model=list[MessageOut])
async def get_messages(session_id: uuid.UUID, current_user: User = Depends(verify_token), db: AsyncSession = Depends(get_db)):
    sess = (await db.execute(select(ChatSession).where(ChatSession.id == session_id, ChatSession.user_id == current_user.id))).scalar_one_or_none()
    if not sess: raise HTTPException(status_code=404, detail="Session not found")
    msgs = await db.execute(select(ChatMessage).where(ChatMessage.session_id == session_id).order_by(ChatMessage.created_at))
    return msgs.scalars().all()

@router.post("/stream")
async def stream_chat(payload: ChatRequest, current_user: User = Depends(verify_token), db: AsyncSession = Depends(get_db)):
    sess = (await db.execute(select(ChatSession).where(ChatSession.id == payload.session_id, ChatSession.user_id == current_user.id))).scalar_one_or_none()
    if not sess: raise HTTPException(status_code=404, detail="Session not found")

    history_msgs = (await db.execute(select(ChatMessage).where(ChatMessage.session_id == payload.session_id).order_by(ChatMessage.created_at))).scalars().all()
    lc_history = [HumanMessage(content=m.content) if m.role == MessageRole.user else AIMessage(content=m.content) for m in history_msgs]

    user_msg = ChatMessage(session_id=payload.session_id, role=MessageRole.user, content=payload.message)
    db.add(user_msg)
    if sess.title == "New Chat":
        await db.execute(update(ChatSession).where(ChatSession.id == payload.session_id).values(title=payload.message[:80].strip()))
    await db.commit()

    collected = []

    async def event_gen():
        chain = get_rag_chain()
        start = time.monotonic()
        try:
            for chunk in chain.stream({"input": payload.message, "chat_history": lc_history}):
                if "answer" in chunk:
                    token = chunk["answer"]
                    collected.append(token)
                    yield f"data: {token.replace(chr(10), chr(92)+'n')}\n\n"
            yield "data: [DONE]\n\n"
            logger.info("Stream done", extra={"user_id": str(current_user.id), "session_id": str(payload.session_id), "latency_ms": int((time.monotonic()-start)*1000), "status_code": 200})
        except Exception as exc:
            logger.error("Stream error: %s", str(exc), extra={"user_id": str(current_user.id), "session_id": str(payload.session_id), "latency_ms": None, "status_code": 500})
            yield f"data: [ERROR] {str(exc)}\n\n"
            return
        full = "".join(collected)
        if full:
            async with AsyncSessionLocal() as s:
                s.add(ChatMessage(session_id=payload.session_id, role=MessageRole.assistant, content=full))
                await s.commit()

    return StreamingResponse(event_gen(), media_type="text/event-stream", headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"})
