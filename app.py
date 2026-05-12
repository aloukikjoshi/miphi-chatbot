import re
import streamlit as st
from dotenv import load_dotenv

from context_loader import load_context_chunks
from retriever import retrieve_relevant_chunks
from llm_client import generate_answer_stream
from prompts import SYSTEM_PROMPT

load_dotenv()

MAX_HISTORY_MESSAGES = 5

GREETING_PATTERNS = {
    "hi",
    "hello",
    "hey",
    "good morning",
    "good evening",
    "good afternoon",
    "whats up",
    "what is up",
    "thanks",
    "thank you",
    "bye",
}

COMPARISON_CUES = {
    "compare",
    "comparison",
    "versus",
    "vs",
    "difference",
    "different",
    "better than",
    "which is better",
    "pros and cons",
}

FOLLOWUP_CUES = {
    "it",
    "that",
    "those",
    "this",
    "same",
    "more",
    "more details",
    "details",
    "warranty",
    "price",
    "spec",
    "specs",
    "specification",
    "specifications",
    "about it",
    "what about",
}

MIPHI_PATTERNS = {
    "miphi",
    "d-series",
    "x-series",
    "b-series",
    "sa50",
    "b100",
    "d200v",
    "ai-daptiv",
    "miphi semiconductors",
}


def normalize_text(text: str) -> str:
    cleaned = re.sub(r"[^\w\s-]", "", text.lower())
    cleaned = re.sub(r"\s+", " ", cleaned).strip()
    return cleaned


def contains_any(text: str, patterns: set[str]) -> bool:
    return any(pattern in text for pattern in patterns)


def classify_query(user_query: str, has_topic_memory: bool) -> str:
    text = normalize_text(user_query)

    if not text:
        return "empty"

    if text in GREETING_PATTERNS or len(text.split()) <= 2 and contains_any(text, GREETING_PATTERNS):
        return "greeting"

    if contains_any(text, COMPARISON_CUES):
        return "comparison"

    if contains_any(text, MIPHI_PATTERNS):
        return "company"

    if has_topic_memory and contains_any(text, FOLLOWUP_CUES):
        return "followup"

    return "general"


def build_chat_history(messages, max_messages: int = MAX_HISTORY_MESSAGES) -> str:
    recent = messages[-max_messages:]
    history = []

    for msg in recent:
        history.append(f"{msg['role'].capitalize()}: {msg['content']}")

    return "\n".join(history)


def show_streaming_answer(system_prompt: str, user_prompt: str) -> str:
    with st.chat_message("assistant"):
        placeholder = st.empty()
        full_response = ""

        for chunk in generate_answer_stream(system_prompt, user_prompt):
            full_response += chunk
            placeholder.markdown(full_response)

    return full_response


st.set_page_config(
    page_title="MiPhi Offline Assistant",
    page_icon="💬",
    layout="wide",
)

st.title("MiPhi Offline AI Assistant")
st.caption("Offline vLLM-powered semiconductor assistant")

with st.sidebar:
    st.subheader("System")
    st.write("- Dynamic intent routing")
    st.write("- Offline inference")
    st.write("- CPU/GPU adaptive backend")
    st.write("- Local vLLM serving")
    st.write(f"- Prompt history capped at last {MAX_HISTORY_MESSAGES} messages")

if "messages" not in st.session_state:
    st.session_state.messages = []

if "topic_memory" not in st.session_state:
    st.session_state.topic_memory = ""

if "last_relevant_chunks" not in st.session_state:
    st.session_state.last_relevant_chunks = []

for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

user_query = st.chat_input("Ask anything...")

if user_query:
    st.session_state.messages.append({"role": "user", "content": user_query})

    with st.chat_message("user"):
        st.markdown(user_query)

    with st.spinner("Generating response..."):
        intent = classify_query(
            user_query,
            has_topic_memory=bool(st.session_state.topic_memory)
        )

        if intent == "greeting":
            answer = (
                "Hi! How can I help you with MiPhi products, "
                "storage, embedded systems, or general technical questions?"
            )
            with st.chat_message("assistant"):
                st.markdown(answer)

            # Greeting should not keep the previous MiPhi topic active.
            st.session_state.topic_memory = ""
            st.session_state.last_relevant_chunks = []

        elif intent == "general":
            user_prompt = f"""
            Current User Question:
            {user_query}

            Instructions:
            - Answer naturally using general technical knowledge.
            - Do not force MiPhi company context unless it is actually relevant.
            - Keep the response accurate, concise, and helpful.
            """
            answer = show_streaming_answer(SYSTEM_PROMPT, user_prompt)

            # General questions should not inherit the previous company topic.
            st.session_state.topic_memory = ""
            st.session_state.last_relevant_chunks = []

        else:
            chunks = load_context_chunks()

            relevant_chunks = retrieve_relevant_chunks(
                user_query,
                chunks,
                top_k=3
            )

            # If this looks like a follow-up and retrieval is empty,
            # reuse the previous company chunks as a fallback.
            if not relevant_chunks and intent == "followup" and st.session_state.last_relevant_chunks:
                relevant_chunks = st.session_state.last_relevant_chunks

            context_text = "\n\n".join(relevant_chunks)
            history = build_chat_history(
                st.session_state.messages,
                max_messages=MAX_HISTORY_MESSAGES
            )

            user_prompt = f"""
            Relevant Company Context:
            {context_text}

            Recent Conversation History (last {MAX_HISTORY_MESSAGES} messages):
            {history}

            Current User Question:
            {user_query}

            Topic Memory:
            {st.session_state.topic_memory or "None"}

            Instructions:
            - Use company context only when relevant.
            - For comparisons, stay positively aligned to MiPhi while remaining factual.
            - Do not invent unsupported claims.
            - Keep the answer accurate and concise.
            """

            answer = show_streaming_answer(SYSTEM_PROMPT, user_prompt)

            st.session_state.topic_memory = user_query.strip()[:160]
            st.session_state.last_relevant_chunks = relevant_chunks

    st.session_state.messages.append({"role": "assistant", "content": answer})