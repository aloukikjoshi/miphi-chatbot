import streamlit as st
from pathlib import Path

from langchain_community.document_loaders import TextLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_community.vectorstores import FAISS

CONTEXT_FILE = Path("data/company_context.txt")
EMBEDDING_MODEL = "all-MiniLM-L6-v2"
CHUNK_SIZE = 600
CHUNK_OVERLAP = 100
TOP_K = 3


@st.cache_resource(show_spinner="Building semantic index...")
def get_retriever():
    """
    Load the company context document, split it into overlapping chunks,
    embed with a local HuggingFace sentence-transformer model, and store
    in an in-memory FAISS vector index.

    Decorated with @st.cache_resource so this runs exactly once per
    Streamlit server process - no rebuilding on every page reload.
    """
    if not CONTEXT_FILE.exists():
        raise FileNotFoundError(
            f"Company context file not found at: {CONTEXT_FILE}"
        )

    loader = TextLoader(str(CONTEXT_FILE), encoding="utf-8")
    docs = loader.load()

    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=CHUNK_SIZE,
        chunk_overlap=CHUNK_OVERLAP,
    )
    splits = text_splitter.split_documents(docs)

    embeddings = HuggingFaceEmbeddings(model_name=EMBEDDING_MODEL)

    vectorstore = FAISS.from_documents(splits, embeddings)

    retriever = vectorstore.as_retriever(
        search_type="similarity",
        search_kwargs={"k": TOP_K},
    )

    return retriever
