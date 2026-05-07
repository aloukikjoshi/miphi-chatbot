import streamlit as st
from dotenv import load_dotenv

from context_loader import load_context
from llm_client import generate_answer
from prompts import SYSTEM_PROMPT

load_dotenv()

st.set_page_config(
    page_title="MiPhi Offline Assistant",
    page_icon="💬",
    layout="wide",
)

st.title("MiPhi Offline Website Assistant")
st.caption("Local vLLM chatbot using direct context injection")

with st.sidebar:
    st.subheader("Runtime Notes")
    st.write("- Model runs locally through vLLM")
    st.write("- No vector database is used")
    st.write("- Answers depend on `data/company_context.txt`")
    st.write("- Offline after the first model download")

if "messages" not in st.session_state:
    st.session_state.messages = []

for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

user_query = st.chat_input("Ask about MiPhi products, use cases, or support...")

if user_query:
    st.session_state.messages.append({"role": "user", "content": user_query})

    with st.chat_message("user"):
        st.markdown(user_query)

    with st.spinner("Loading local context and generating response..."):
        company_context = load_context()

        if not company_context:
            answer = (
                "The local company context file is empty. "
                "Please add MiPhi public information into `data/company_context.txt`."
            )
        else:
            user_prompt = f"""
Company Context:
{company_context}

User Question:
{user_query}

Answer using only the company context above.
"""
            answer = generate_answer(SYSTEM_PROMPT, user_prompt)

    with st.chat_message("assistant"):
        st.markdown(answer)

    st.session_state.messages.append({"role": "assistant", "content": answer})