import os

import streamlit as st
from dotenv import load_dotenv

from langchain_openai import ChatOpenAI
from langchain.chains import create_history_aware_retriever, create_retrieval_chain
from langchain.chains.combine_documents import create_stuff_documents_chain

from prompts import CONTEXTUALIZE_Q_PROMPT, QA_PROMPT

load_dotenv()

VLLM_BASE_URL = os.getenv("VLLM_BASE_URL", "http://vllm:8000/v1")
VLLM_MODEL = os.getenv("VLLM_MODEL", "meta-llama/Llama-3.2-1B-Instruct")


@st.cache_resource(show_spinner="Connecting to LLM backend...")
def get_llm():
    """
    Return a LangChain ChatOpenAI client pointing at the local vLLM backend.
    Cached so the client object is reused across all Streamlit reruns.
    """
    return ChatOpenAI(
        base_url=VLLM_BASE_URL,
        api_key="EMPTY",
        model=VLLM_MODEL,
        temperature=0.3,
        max_tokens=512,
        streaming=True,
    )


def get_rag_chain(retriever):
    """
    Assemble the full history-aware RAG chain:

    1. History-Aware Retriever
       Uses CONTEXTUALIZE_Q_PROMPT to ask the LLM to rewrite the current
       user question as a standalone question before retrieval.
       Fixes pronoun/reference failures like
       'What is its capacity?' -> 'What is the B100 SSD storage capacity?'

    2. Document-Stuffing QA Chain
       Injects retrieved chunks as {context} into QA_PROMPT together with
       the full alternating chat history, producing the final streamed answer.

    3. Retrieval Chain
       Wires both sub-chains into a single callable that accepts
       {'input': str, 'chat_history': list[BaseMessage]} and returns
       {'answer': str, 'context': list[Document], ...}
    """
    llm = get_llm()

    history_aware_retriever = create_history_aware_retriever(
        llm, retriever, CONTEXTUALIZE_Q_PROMPT
    )

    question_answer_chain = create_stuff_documents_chain(llm, QA_PROMPT)

    rag_chain = create_retrieval_chain(
        history_aware_retriever, question_answer_chain
    )

    return rag_chain
