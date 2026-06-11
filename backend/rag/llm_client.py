import os
from functools import lru_cache
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langchain_classic.chains import create_history_aware_retriever, create_retrieval_chain
from langchain_classic.chains.combine_documents import create_stuff_documents_chain
from backend.rag.prompts import CONTEXTUALIZE_Q_PROMPT, QA_PROMPT
from backend.rag.retriever import get_retriever

load_dotenv()
VLLM_BASE_URL = os.getenv("VLLM_BASE_URL", "http://vllm:8000/v1")
VLLM_MODEL = os.getenv("VLLM_MODEL", "meta-llama/Llama-3.2-1B-Instruct")

@lru_cache(maxsize=1)
def get_llm():
    return ChatOpenAI(base_url=VLLM_BASE_URL, api_key="EMPTY", model=VLLM_MODEL, temperature=0.3, max_tokens=512, streaming=True)

@lru_cache(maxsize=1)
def get_rag_chain():
    llm = get_llm()
    retriever = get_retriever()
    return create_retrieval_chain(
        create_history_aware_retriever(llm, retriever, CONTEXTUALIZE_Q_PROMPT),
        create_stuff_documents_chain(llm, QA_PROMPT)
    )
