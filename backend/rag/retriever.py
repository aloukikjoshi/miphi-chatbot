from functools import lru_cache
from pathlib import Path
from langchain_community.document_loaders import TextLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_community.vectorstores import FAISS

CONTEXT_FILE = Path("data/company_context.txt")

@lru_cache(maxsize=1)
def get_retriever():
    if not CONTEXT_FILE.exists():
        raise FileNotFoundError(f"Context file not found: {CONTEXT_FILE}")
    loader = TextLoader(str(CONTEXT_FILE), encoding="utf-8")
    splits = RecursiveCharacterTextSplitter(chunk_size=600, chunk_overlap=100).split_documents(loader.load())
    vectorstore = FAISS.from_documents(splits, HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2"))
    return vectorstore.as_retriever(search_type="similarity", search_kwargs={"k": 3})
