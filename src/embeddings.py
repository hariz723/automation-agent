"""Hugging Face Embeddings module for semantic search and token reduction."""

import math
import re

from langchain_core.embeddings import Embeddings

from src.config import Config


class FastDeterministicEmbeddings(Embeddings):
    """Lightweight deterministic embeddings fallback for offline/test environments.
    Uses n-gram bag-of-words hashing to generate normalized dense vector representations.
    """

    def __init__(self, dim: int = 128):
        self.dim = dim

    def _embed_text(self, text: str) -> list[float]:
        words = re.findall(r"\w+", text.lower())
        vec = [0.0] * self.dim
        if not words:
            return vec

        for word in words:
            idx = hash(word) % self.dim
            vec[idx] += 1.0

        norm = math.sqrt(sum(x * x for x in vec))
        if norm > 0:
            vec = [x / norm for x in vec]
        return vec

    def embed_documents(self, texts: list[str]) -> list[list[float]]:
        return [self._embed_text(t) for t in texts]

    def embed_query(self, text: str) -> list[float]:
        return self._embed_text(text)


def get_hf_embeddings(model_name: str | None = None) -> Embeddings:
    """Return Hugging Face embeddings model.

    Priority:
      1. HuggingFaceEndpointEmbeddings if HF token is configured (cloud API, zero local disk).
      2. HuggingFaceEmbeddings if sentence-transformers is installed locally.
      3. FastDeterministicEmbeddings fallback if offline/no token provided.
    """
    model = model_name or Config.HF_EMBEDDING_MODEL
    token = Config.HUGGINGFACEHUB_API_TOKEN

    if token:
        try:
            from langchain_huggingface import HuggingFaceEndpointEmbeddings

            return HuggingFaceEndpointEmbeddings(
                model=model,
                huggingfacehub_api_token=token,
            )
        except Exception:
            pass

    try:
        from langchain_huggingface import HuggingFaceEmbeddings

        return HuggingFaceEmbeddings(model_name=model)
    except Exception:
        pass

    return FastDeterministicEmbeddings()


def cosine_similarity(vec1: list[float], vec2: list[float]) -> float:
    """Compute cosine similarity between two numeric vectors."""
    dot = sum(a * b for a, b in zip(vec1, vec2))
    norm1 = math.sqrt(sum(a * a for a in vec1))
    norm2 = math.sqrt(sum(b * b for b in vec2))
    if norm1 == 0 or norm2 == 0:
        return 0.0
    return dot / (norm1 * norm2)


def chunk_text(text: str, chunk_size: int = 400, overlap: int = 50) -> list[str]:
    """Split text into overlapping semantic chunks (paragraphs/sentences)."""
    paragraphs = [p.strip() for p in text.split("\n\n") if p.strip()]
    chunks = []

    for para in paragraphs:
        if len(para) <= chunk_size:
            chunks.append(para)
        else:
            # Sub-split long paragraphs by sentence or words
            words = para.split()
            current_chunk: list[str] = []
            current_len = 0

            for word in words:
                current_chunk.append(word)
                current_len += len(word) + 1
                if current_len >= chunk_size:
                    chunks.append(" ".join(current_chunk))
                    # Keep overlap words
                    overlap_words = current_chunk[-max(1, overlap // 10) :]
                    current_chunk = list(overlap_words)
                    current_len = sum(len(w) + 1 for w in current_chunk)

            if current_chunk:
                chunks.append(" ".join(current_chunk))

    return chunks if chunks else [text.strip()]


def semantic_search_chunks(
    query: str,
    chunks: list[str],
    embeddings: Embeddings | None = None,
    top_k: int = 3,
) -> list[dict]:
    """Rank chunks by cosine similarity to query using embeddings."""
    if not chunks:
        return []

    emb_model = embeddings or get_hf_embeddings()
    query_vec = emb_model.embed_query(query)
    doc_vectors = emb_model.embed_documents(chunks)

    scored_chunks = []
    for i, (chunk, vec) in enumerate(zip(chunks, doc_vectors)):
        sim = cosine_similarity(query_vec, vec)
        scored_chunks.append(
            {
                "chunk_id": i + 1,
                "content": chunk,
                "similarity": round(sim, 4),
            }
        )

    # Sort descending by similarity
    scored_chunks.sort(key=lambda x: x["similarity"], reverse=True)
    return scored_chunks[:top_k]
