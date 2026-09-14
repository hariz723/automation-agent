"""Hugging Face Embedding tools for token-efficient retrieval."""

from pathlib import Path

from langchain_core.tools import tool

from src.config import Config
from src.embeddings import chunk_text, get_hf_embeddings, semantic_search_chunks


@tool
def semantic_search_text(text: str, query: str, top_k: int = 3) -> str:
    """Split a long text into chunks, compute Hugging Face embeddings, and return only the top-k most relevant chunks to reduce prompt token size.
    
    Args:
        text: The large text content to search within.
        query: What specific information or answer you are looking for.
        top_k: Number of most relevant snippets to return (default: 3).
    """
    if not text.strip():
        return "Error: Input text is empty."

    chunks = chunk_text(text, chunk_size=450, overlap=50)
    if not chunks:
        return text

    emb_model = get_hf_embeddings()
    results = semantic_search_chunks(query=query, chunks=chunks, embeddings=emb_model, top_k=top_k)

    # Token reduction statistics estimation (~4 chars per token)
    orig_chars = len(text)
    orig_tokens = orig_chars // 4
    retrieved_text = "\n\n---\n\n".join(r["content"] for r in results)
    retrieved_tokens = len(retrieved_text) // 4
    savings_pct = max(0, round((1 - (retrieved_tokens / max(1, orig_tokens))) * 100))

    output = [
        f"📊 [Token Reduction via HF Embeddings: ~{orig_tokens} tokens ➡️ ~{retrieved_tokens} tokens ({savings_pct}% saved)]\n",
        "Relevant Snippets:",
    ]
    for r in results:
        output.append(f"[Snippet #{r['chunk_id']} | Relevance: {r['similarity']}]\n{r['content']}")

    return "\n\n".join(output)


@tool
def semantic_search_file(filepath: str, query: str, top_k: int = 3) -> str:
    """Read a large workspace file, compute Hugging Face embeddings, and retrieve only the top-k relevant sections instead of passing the entire file to save tokens.
    
    Args:
        filepath: Relative or absolute path to the file.
        query: The question, topic, or function name you need from the file.
        top_k: Number of most relevant sections to retrieve (default: 3).
    """
    try:
        path = Path(filepath)
        if not path.is_absolute():
            path = Config.WORKSPACE_DIR / path

        if not path.exists():
            return f"Error: File does not exist: {filepath}"

        with open(path, encoding="utf-8", errors="replace") as f:
            content = f.read()

        return semantic_search_text.invoke({
            "text": content,
            "query": query,
            "top_k": top_k,
        })

    except Exception as e:
        return f"Error reading and embedding file {filepath}: {e!s}"
