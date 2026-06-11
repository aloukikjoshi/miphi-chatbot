import streamlit as st
from dotenv import load_dotenv

from langchain_core.messages import HumanMessage, AIMessage

from retriever import get_retriever
from llm_client import get_rag_chain

load_dotenv()

# ---------------------------------------------------------------------------
# Page configuration
# ---------------------------------------------------------------------------
st.set_page_config(
    page_title="MiPhi AI Assistant",
    page_icon="??",
    layout="wide",
)

st.title("MiPhi Offline AI Assistant")
st.caption("Offline vLLM-powered semiconductor assistant | LangChain RAG")

with st.sidebar:
    st.subheader("System")
    st.write("- Semantic FAISS vector search")
    st.write("- History-aware query rewriting")
    st.write("- Multi-turn LangChain RAG chain")
    st.write("- Offline vLLM inference (CPU/GPU)")
    st.write("- Streaming responses")

    if st.button("??? Clear conversation", use_container_width=True):
        st.session_state.chat_history = []
        st.session_state.messages = []
        st.rerun()

# ---------------------------------------------------------------------------
# One-time startup: build the FAISS index and RAG chain (cached)
# ---------------------------------------------------------------------------
retriever = get_retriever()
rag_chain = get_rag_chain(retriever)

# ---------------------------------------------------------------------------
# Session state
# ---------------------------------------------------------------------------
# messages       - list of {'role': str, 'content': str} for display
# chat_history   - list of LangChain BaseMessage objects (HumanMessage /
#                  AIMessage) passed directly into the RAG chain so the LLM
#                  receives a properly structured multi-turn conversation
# ---------------------------------------------------------------------------
if "messages" not in st.session_state:
    st.session_state.messages = []

if "chat_history" not in st.session_state:
    st.session_state.chat_history = []

# ---------------------------------------------------------------------------
# Render existing conversation
# ---------------------------------------------------------------------------
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# ---------------------------------------------------------------------------
# Handle new user input
# ---------------------------------------------------------------------------
user_query = st.chat_input("Ask anything...")

if user_query:
    st.session_state.messages.append({"role": "user", "content": user_query})
    with st.chat_message("user"):
        st.markdown(user_query)

    # -----------------------------------------------------------------------
    # Stream the RAG chain response
    # chat_history is passed WITHOUT the current message so the retriever
    # uses only prior turns when rewriting the query.
    # -----------------------------------------------------------------------
    with st.chat_message("assistant"):
        placeholder = st.empty()
        full_response = ""

        try:
            for chunk in rag_chain.stream(
                {
                    "input": user_query,
                    "chat_history": st.session_state.chat_history,
                }
            ):
                # create_retrieval_chain streams partial dicts;
                # the answer delta lives under the "answer" key
                if "answer" in chunk:
                    full_response += chunk["answer"]
                    placeholder.markdown(full_response + "?")

            placeholder.markdown(full_response)

        except Exception as e:
            full_response = (
                f"?? Unable to generate a response.\n\n"
                f"**Error:** {str(e)}\n\n"
                "Please check that the vLLM backend is running and reachable."
            )
            placeholder.markdown(full_response)

    # -----------------------------------------------------------------------
    # Update both storage formats
    # -----------------------------------------------------------------------
    st.session_state.messages.append(
        {"role": "assistant", "content": full_response}
    )

    # Append as structured LangChain messages for the next turn
    st.session_state.chat_history.append(HumanMessage(content=user_query))
    st.session_state.chat_history.append(AIMessage(content=full_response))
