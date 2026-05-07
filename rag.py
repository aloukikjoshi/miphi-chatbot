from __future__ import annotations

import json
import os
from dataclasses import dataclass
from pathlib import Path

import numpy as np
from sentence_transformers import SentenceTransformer
from vllm import LLM, SamplingParams

BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"
KV_CACHE_PATH = DATA_DIR / "kv_cache.json"

EMBED_MODEL_NAME = os.getenv("EMBED_MODEL", "sentence-transformers/all-MiniLM-L6-v2")
VLLM_MODEL_PATH = os.getenv("VLLM_MODEL_PATH", "llama3-8b")


@dataclass
class SearchHit:
    text: str
    source: str
    title: str
    chunk_id: str
    score: float | None = None


class MiPhiRAG:
    def __init__(self) -> None:
        DATA_DIR.mkdir(parents=True, exist_ok=True)

        self.embedder = SentenceTransformer(EMBED_MODEL_NAME)
        self.kv_cache_file = KV_CACHE_PATH
        self.kv_items = self._load_kv_cache()

        self.llm = LLM(model=VLLM_MODEL_PATH)

    def _load_kv_cache(self) -> list[dict]:
        if self.kv_cache_file.exists():
            return json.loads(self.kv_cache_file.read_text(encoding="utf-8"))
        return []

    def _save_kv_cache(self) -> None:
        self.kv_cache_file.write_text(json.dumps(self.kv_items, indent=2), encoding="utf-8")

    def embed_texts(self, texts: list[str]) -> list[list[float]]:
        vectors = self.embedder.encode(texts, normalize_embeddings=True)
        return vectors.tolist()

    def add_chunks(self, chunks: list[dict[str, object]]) -> None:
        if not chunks:
            return

        texts = [c["text"] for c in chunks]
        embeddings = self.embed_texts(texts)

        for chunk, embedding in zip(chunks, embeddings):
            self.kv_items.append(
                {
                    "id": chunk["id"],
                    "text": chunk["text"],
                    "title": chunk["title"],
                    "source": chunk.get("source", ""),
                    "url": chunk.get("url", ""),
                    "chunk_index": chunk.get("chunk_index", 0),
                    "embedding": embedding,
                }
            )

        self._save_kv_cache()

    def search(self, query: str, k: int = 4) -> list[SearchHit]:
        if not self.kv_items:
            return []

        query_vector = np.array(self.embed_texts([query])[0], dtype=np.float32)
        embeddings = np.array([item["embedding"] for item in self.kv_items], dtype=np.float32)
        scores = embeddings @ query_vector
        norms = np.linalg.norm(embeddings, axis=1) * np.linalg.norm(query_vector)
        norms = np.where(norms == 0.0, 1e-8, norms)
        similarities = (scores / norms).tolist()

        best_indexes = sorted(range(len(similarities)), key=lambda i: similarities[i], reverse=True)[:k]
        hits: list[SearchHit] = []

        for idx in best_indexes:
            item = self.kv_items[idx]
            hits.append(
                SearchHit(
                    text=item["text"],
                    source=item.get("url", ""),
                    title=item.get("title", ""),
                    chunk_id=item["id"],
                    score=float(similarities[idx]),
                )
            )

        return hits

    def build_prompt(self, query: str, history: list[dict[str, str]], hits: list[SearchHit]) -> str:
        context_blocks = []
        for i, hit in enumerate(hits, start=1):
            context_blocks.append(
                f"[Source {i}]\nTitle: {hit.title}\nURL: {hit.source}\nContent:\n{hit.text}"
            )

        context_text = "\n\n".join(context_blocks) if context_blocks else "No relevant public context found."
        history_text = "\n".join(
            f"{turn['role'].capitalize()}: {turn['content']}"
            for turn in history[-6:]
            if turn["role"] in {"user", "assistant"}
        )

        return (
            "You are MiPhi's public website assistant. Answer using only the public context below. "
            "If the context is insufficient, say you do not have enough public information and suggest contacting MiPhi support. "
            "Keep responses concise, friendly, and helpful."
            "\n\n"
            f"{history_text}\n\n"
            f"Question: {query}\n\n"
            f"Relevant public context:\n{context_text}\n\n"
            "Answer:"
        )

    def chat(self, query: str, history: list[dict[str, str]], hits: list[SearchHit]) -> str:
        prompt = self.build_prompt(query=query, history=history, hits=hits)
        sampling_params = SamplingParams(temperature=0.2, max_tokens=512, top_p=0.95)

        request = [
            {
                "id": "miphi",
                "prompt": prompt,
                "sampling_params": sampling_params,
            }
        ]

        outputs = self.llm.generate(request)
        return outputs[0].outputs[0].text.strip()

    def answer(self, query: str, history: list[dict[str, str]] | None = None, k: int = 4) -> tuple[str, list[SearchHit]]:
        history = history or []
        hits = self.search(query, k=k)

        if not hits:
            return (
                "I could not find enough relevant public information for that question. "
                "Please check MiPhi’s official website or contact support for more details.",
                [],
            )

        try:
            answer = self.chat(query=query, history=history, hits=hits)
        except Exception as exc:
            answer = (
                f"I could not generate a local response right now ({exc}). "
                "Please make sure your local vLLM model is available and try again."
            )

        return answer, hits