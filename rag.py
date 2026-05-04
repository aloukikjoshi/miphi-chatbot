from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any
from urllib import response

import chromadb
import requests
from sentence_transformers import SentenceTransformer

from groq import Groq
import os

GROQ_API_KEY = os.getenv("GROQ_API_KEY")

client = Groq(api_key=GROQ_API_KEY)

BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"
CHROMA_DIR = DATA_DIR / "chroma_db"

COLLECTION_NAME = os.getenv("CHROMA_COLLECTION", "miphi_public_knowledge")
EMBED_MODEL_NAME = os.getenv("EMBED_MODEL", "sentence-transformers/all-MiniLM-L6-v2")
OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "llama3.1:8b")


@dataclass
class SearchHit:
    text: str
    source: str
    title: str
    chunk_id: str
    distance: float | None = None


class MiPhiRAG:
    def __init__(self) -> None:
        DATA_DIR.mkdir(parents=True, exist_ok=True)
        CHROMA_DIR.mkdir(parents=True, exist_ok=True)

        self.client = chromadb.PersistentClient(path=str(CHROMA_DIR))
        self.collection = self.client.get_or_create_collection(name=COLLECTION_NAME)
        self.embedder = SentenceTransformer(EMBED_MODEL_NAME)

    def embed_texts(self, texts: list[str]) -> list[list[float]]:
        vectors = self.embedder.encode(texts, normalize_embeddings=True)
        return vectors.tolist()

    def add_chunks(self, chunks: list[dict[str, Any]]) -> None:
        if not chunks:
            return

        ids = [c["id"] for c in chunks]
        docs = [c["text"] for c in chunks]
        metas = [
            {
                "source": c.get("source", ""),
                "title": c.get("title", ""),
                "url": c.get("url", ""),
                "chunk_index": str(c.get("chunk_index", 0)),
            }
            for c in chunks
        ]
        embeddings = self.embed_texts(docs)

        self.collection.upsert(
            ids=ids,
            documents=docs,
            metadatas=metas,
            embeddings=embeddings,
        )

    def search(self, query: str, k: int = 4) -> list[SearchHit]:
        query_embedding = self.embed_texts([query])[0]
        result = self.collection.query(
            query_embeddings=[query_embedding],
            n_results=k,
            include=["documents", "metadatas", "distances"],
        )

        hits: list[SearchHit] = []
        documents = result.get("documents", [[]])[0]
        metadatas = result.get("metadatas", [[]])[0]
        distances = result.get("distances", [[]])[0]

        for doc, meta, dist in zip(documents, metadatas, distances):
            hits.append(
                SearchHit(
                    text=doc or "",
                    source=(meta or {}).get("url", ""),
                    title=(meta or {}).get("title", ""),
                    chunk_id="",
                    distance=float(dist) if dist is not None else None,
                )
            )
        return hits

    def build_messages(self, query: str, history: list[dict[str, str]], hits: list[SearchHit]) -> list[dict[str, str]]:
        context_blocks = []
        for i, hit in enumerate(hits, start=1):
            context_blocks.append(
                f"[Source {i}]\nTitle: {hit.title}\nURL: {hit.source}\nContent:\n{hit.text}"
            )

        context_text = "\n\n".join(context_blocks) if context_blocks else "No relevant public context found."

        system_prompt = (
            "You are MiPhi's public website assistant.\n"
            "Answer using ONLY the provided context and public company/product information.\n"
            "Keep responses concise, friendly, and helpful.\n"
            "Use a marketing-friendly tone without being pushy.\n"
            "If the context is insufficient, say you do not have enough public information and suggest contacting MiPhi support.\n"
            "Never reveal private, internal, confidential, or speculative information.\n"
            "When useful, summarize product benefits, use cases, and differences clearly."
        )

        messages: list[dict[str, str]] = [{"role": "system", "content": system_prompt}]

        # Keep short conversation memory
        for turn in history[-6:]:
            if turn["role"] in {"user", "assistant"}:
                messages.append({"role": turn["role"], "content": turn["content"]})

        messages.append(
            {
                "role": "user",
                "content": (
                    f"Question: {query}\n\n"
                    f"Relevant public context:\n{context_text}\n\n"
                    "Write the best answer based on the context."
                ),
            }
        )
        return messages
    
    def chat(self, messages):
        response = client.chat.completions.create(
            model="llama3-8b-8192",
            messages=messages,
            temperature=0.2,
            )
        return response.choices[0].message.content

    def answer(self, query: str, history: list[dict[str, str]] | None = None, k: int = 4) -> tuple[str, list[SearchHit]]:
        history = history or []
        hits = self.search(query, k=k)

        if not hits:
            return (
                "I could not find enough relevant public information for that question. "
                "Please check MiPhi’s official website or contact support for more details.",
                [],
            )

        messages = self.build_messages(query=query, history=history, hits=hits)

        try:
            answer = self.chat(messages)
        except requests.RequestException as exc:
            answer = (
                f"I could not reach the local model runtime right now ({exc}). "
                "Please make sure Ollama is running and try again."
            )

        return answer, hits