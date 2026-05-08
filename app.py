import streamlit as st
from dotenv import load_dotenv
import requests
from context_loader import load_context
from llm_client import generate_answer_stream
from prompts import SYSTEM_PROMPT

load_dotenv()


def build_chat_history(messages, max_messages=6):
    history = []

    recent_messages = messages[-max_messages:]

    for msg in recent_messages:
        history.append(
            f"{msg['role'].capitalize()}: {msg['content']}"
        )

    return "\n".join(history)


st.set_page_config(
    page_title="MiPhi Offline Assistant",
    page_icon="💬",
    layout="wide",
)

st.title("MiPhi Offline Website Assistant")

st.caption(
    "Offline vLLM-powered semiconductor assistant"
)

with st.sidebar:
    st.divider()
    st.subheader("Backend Status")
    try:
        response = requests.get(
            "http://vllm:8000/health",
            timeout=2
        )

        if response.status_code == 200:
            st.success("vLLM Backend Connected")
        else:
            st.warning("Backend responding unexpectedly")
    except:
            st.error("vLLM Backend Not Reachable")
    st.divider()
    st.subheader("Suggested Questions")
    st.write("• Hello")
    st.write("• What does MiPhi do?")
    st.write("• Explain SSDs")
    st.write("• What is edge AI?")
    st.write("• Explain embedded systems")

if "messages" not in st.session_state:
    st.session_state.messages = []

for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

user_query = st.chat_input(
    "Ask about MiPhi products or technology..."
)

if user_query:

    st.session_state.messages.append(
        {
            "role": "user",
            "content": user_query
        }
    )

    with st.chat_message("user"):
        st.markdown(user_query)

    company_context = load_context()

    chat_history = build_chat_history(
        st.session_state.messages
    )

    user_prompt = f"""
Company Context:
{company_context}

Conversation History:
{chat_history}

Current User Question:
{user_query}

Instructions:
- Use company context for MiPhi-specific answers
- Use general technical knowledge when appropriate
- Maintain conversation continuity
"""

    with st.chat_message("assistant"):

        response_placeholder = st.empty()

        full_response = ""

        for chunk in generate_answer_stream(
            SYSTEM_PROMPT,
            user_prompt
        ):

            full_response += chunk

            response_placeholder.markdown(
                full_response
            )

    st.session_state.messages.append(
        {
            "role": "assistant",
            "content": full_response
        }
    )