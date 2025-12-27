from pathlib import Path
import json
import os

import faiss
import numpy as np
from dotenv import load_dotenv
from openai import OpenAI
from pypdf import PdfReader

# === config ===
load_dotenv()
client = OpenAI(api_key=os.environ["API_KEY"])

SOURCE_DIR = Path("rag_source")
RAG_DIR = Path("rag_store")
RAG_DIR.mkdir(exist_ok=True)

INDEX_PATH = RAG_DIR / "index.faiss"
CHUNKS_PATH = RAG_DIR / "chunks.json"

CHUNK_WORDS = 450
OVERLAP_WORDS = 80


def read_all_pdfs() -> str:
    texts = []
    pdfs = sorted(SOURCE_DIR.glob("*.pdf"))
    if not pdfs:
        raise FileNotFoundError(f"Geen PDF's gevonden in {SOURCE_DIR.resolve()}")

    for pdf in pdfs:
        reader = PdfReader(str(pdf))
        for page in reader.pages:
            t = page.extract_text() or ""
            t = t.strip()
            if t:
                # bronlabel helpt later bij debugging/kwaliteit
                texts.append(f"[BRON: {pdf.name}]\n{t}")
    return "\n\n".join(texts)


def chunk_text(text: str) -> list[str]:
    words = text.split()
    chunks = []
    step = max(1, CHUNK_WORDS - OVERLAP_WORDS)

    for start in range(0, len(words), step):
        chunk = " ".join(words[start : start + CHUNK_WORDS]).strip()
        if len(chunk) >= 200:  # filter mini-fragmenten
            chunks.append(chunk)

    return chunks


def embed_chunks(chunks: list[str]) -> np.ndarray:
    vectors = []
    for i, chunk in enumerate(chunks, start=1):
        resp = client.embeddings.create(
            model="text-embedding-3-small",
            input=[chunk],
        )
        vectors.append(resp.data[0].embedding)
        if i % 25 == 0:
            print(f"  embeddings: {i}/{len(chunks)}")

    return np.array(vectors, dtype="float32")


def main():
    print("PDF's lezen...")
    text = read_all_pdfs()

    print("Chunks maken...")
    chunks = chunk_text(text)
    print(f"  chunks: {len(chunks)}")

    print("Embeddings maken...")
    vectors = embed_chunks(chunks)

    print("FAISS index bouwen...")
    faiss.normalize_L2(vectors)
    index = faiss.IndexFlatIP(vectors.shape[1])
    index.add(vectors)

    faiss.write_index(index, str(INDEX_PATH))
    with open(CHUNKS_PATH, "w", encoding="utf-8") as f:
        json.dump(chunks, f, ensure_ascii=False, indent=2)

    print(f"Klaar: {len(chunks)} chunks opgeslagen in {RAG_DIR}/")


if __name__ == "__main__":
    main()
