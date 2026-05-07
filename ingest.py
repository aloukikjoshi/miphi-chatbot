from __future__ import annotations

import argparse
import hashlib
import io
import re
from pathlib import Path
from typing import Iterable
from urllib.parse import urlparse

import requests
from bs4 import BeautifulSoup
from pypdf import PdfReader

from rag import MiPhiRAG

BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"
RAW_DIR = DATA_DIR / "raw"
PROCESSED_DIR = DATA_DIR / "processed"
SOURCES_FILE = DATA_DIR / "sources.txt"


def read_sources(path: Path) -> list[str]:
    if not path.exists():
        return []
    lines = []
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        lines.append(line)
    return lines


def clean_text(text: str) -> str:
    text = re.sub(r"\r", "\n", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    text = re.sub(r"[ \t]{2,}", " ", text)
    return text.strip()


def extract_html_text(html: str) -> tuple[str, str]:
    soup = BeautifulSoup(html, "html.parser")

    for tag in soup(["script", "style", "nav", "footer", "header", "noscript", "svg", "form"]):
        tag.decompose()

    title = soup.title.get_text(" ", strip=True) if soup.title else "Untitled page"
    text = soup.get_text("\n", strip=True)
    return title, clean_text(text)


def extract_pdf_text(content: bytes) -> tuple[str, str]:
    reader = PdfReader(io.BytesIO(content))
    texts = []
    for page in reader.pages:
        texts.append(page.extract_text() or "")
    text = clean_text("\n".join(texts))
    return "PDF document", text


def fetch_page(url: str) -> tuple[str, str]:
    resp = requests.get(url, timeout=60, headers={"User-Agent": "Mozilla/5.0"})
    resp.raise_for_status()

    content_type = resp.headers.get("Content-Type", "").lower()
    if "pdf" in content_type or url.lower().endswith(".pdf"):
        return extract_pdf_text(resp.content)

    return extract_html_text(resp.text)


def chunk_text(text: str, chunk_size: int = 900, overlap: int = 150) -> list[str]:
    words = text.split()
    if not words:
        return []

    chunks: list[str] = []
    start = 0

    while start < len(words):
        end = min(start + chunk_size, len(words))
        chunk = " ".join(words[start:end]).strip()
        if chunk:
            chunks.append(chunk)
        if end == len(words):
            break
        start = max(0, end - overlap)

    return chunks


def stable_id(source: str, idx: int, text: str) -> str:
    digest = hashlib.sha1(f"{source}|{idx}|{text[:200]}".encode("utf-8")).hexdigest()
    return digest


def build_chunks_from_url(url: str) -> list[dict]:
    title, text = fetch_page(url)
    chunks = chunk_text(text)
    docs = []

    for idx, chunk in enumerate(chunks):
        docs.append(
            {
                "id": stable_id(url, idx, chunk),
                "text": chunk,
                "title": title,
                "source": url,
                "url": url,
                "chunk_index": idx,
            }
        )

    return docs


def main() -> None:
    parser = argparse.ArgumentParser(description="Ingest MiPhi public pages into local KV cache.")
    parser.add_argument(
        "--sources",
        type=str,
        default=str(SOURCES_FILE),
        help="Path to a newline-separated list of allowed public URLs.",
    )
    args = parser.parse_args()

    DATA_DIR.mkdir(parents=True, exist_ok=True)
    RAW_DIR.mkdir(parents=True, exist_ok=True)
    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)

    sources = read_sources(Path(args.sources))
    if not sources:
        print("No sources found. Add public MiPhi URLs to data/sources.txt and run again.")
        return

    rag = MiPhiRAG()
    all_chunks: list[dict] = []

    for url in sources:
        try:
            print(f"Fetching: {url}")
            docs = build_chunks_from_url(url)
            print(f"  -> {len(docs)} chunks")
            all_chunks.extend(docs)
        except Exception as exc:
            print(f"  !! Failed: {url} -> {exc}")

    if not all_chunks:
        print("No chunks were created.")
        return

    rag.add_chunks(all_chunks)
    print(f"Done. Indexed {len(all_chunks)} chunks into local KV cache.")


if __name__ == "__main__":
    main()