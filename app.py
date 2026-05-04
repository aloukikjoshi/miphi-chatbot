from __future__ import annotations

import streamlit as st

from rag import MiPhiRAG

st.set_page_config(page_title="MiPhi Assistant", page_icon="💬", layout="centered")

st.title("MiPhi Public Website Assistant")
st.caption("Text-only assistant for company and product information")

@st.cache_resource
def load_rag() -> MiPhiRAG:
    return MiPhiRAG()

rag = load_rag()

if "messages" not in st.session_state:
    st.session_state.messages = [
        {
            "role": "assistant",
            "content": (
                "Hi, I can help you explore MiPhi products, company information, use cases, "
                "and public support details."
            ),
        }
    ]

for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

query = st.chat_input("Ask about products, company info, or use cases")

if query:
    st.session_state.messages.append({"role": "user", "content": query})

    with st.chat_message("user"):
        st.markdown(query)

    with st.chat_message("assistant"):
        with st.spinner("Thinking..."):
            answer, hits = rag.answer(query=query, history=st.session_state.messages[:-1], k=4)

        st.markdown(answer)

        if hits:
            with st.expander("Sources"):
                for i, hit in enumerate(hits, start=1):
                    st.write(f"**Source {i}:** {hit.title}")
                    st.write(hit.source)
                    st.write(hit.text[:500] + ("..." if len(hit.text) > 500 else ""))

    st.session_state.messages.append({"role": "assistant", "content": answer})