import streamlit as st
from dotenv import load_dotenv

from context_loader import (
    load_context_chunks
)

from retriever import (
    retrieve_relevant_chunks
)

from llm_client import (
    generate_answer_stream
)

from prompts import SYSTEM_PROMPT

load_dotenv()


def build_chat_history(
    messages,
    max_messages=6
):

    recent = messages[-max_messages:]

    history = []

    for msg in recent:

        history.append(
            f"{msg['role'].capitalize()}: "
            f"{msg['content']}"
        )

    return "\n".join(history)


st.set_page_config(
    page_title="MiPhi Offline Assistant",
    page_icon="💬",
    layout="wide",
)

st.title(
    "MiPhi Offline AI Assistant"
)

st.caption(
    "Offline vLLM-powered semiconductor assistant"
)

with st.sidebar:

    st.subheader("System")

    st.write(
        "- Dynamic context retrieval"
    )

    st.write(
        "- Offline inference"
    )

    st.write(
        "- CPU/GPU adaptive backend"
    )

    st.write(
        "- Local vLLM serving"
    )

if "messages" not in st.session_state:
    st.session_state.messages = []

for msg in st.session_state.messages:

    with st.chat_message(
        msg["role"]
    ):

        st.markdown(
            msg["content"]
        )

user_query = st.chat_input(
    "Ask anything..."
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

    with st.spinner(
        "Generating response..."
    ):

        chunks = load_context_chunks()

        relevant_chunks = (
            retrieve_relevant_chunks(
                user_query,
                chunks,
                top_k=3
            )
        )

        context_text = "\n\n".join(
            relevant_chunks
        )

        history = build_chat_history(
            st.session_state.messages
        )

        user_prompt = f"""
Relevant Company Context:
{context_text}

Conversation History:
{history}

Current User Question:
{user_query}

Instructions:
- Use context if relevant
- Otherwise use general knowledge
- Keep answers accurate and concise
"""

        with st.chat_message(
            "assistant"
        ):

            placeholder = st.empty()

            full_response = ""

            for chunk in (
                generate_answer_stream(
                    SYSTEM_PROMPT,
                    user_prompt
                )
            ):

                full_response += chunk

                placeholder.markdown(
                    full_response
                )

    st.session_state.messages.append(
        {
            "role": "assistant",
            "content": full_response
        }
    )