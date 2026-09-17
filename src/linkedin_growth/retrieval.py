"""Custom retriever used instead of Agno's default `knowledge.search()`, which
has two problems: no relevance floor (an unrelated query still returns the
nearest neighbours, causing false duplicates for the Planner) and no grouping
(one document's chunks can fill every result slot). Both are fixed here and
wired in as an agent's `knowledge_retriever`, so no agent instruction changes.
"""

from __future__ import annotations

import os
from typing import TYPE_CHECKING, Any, Callable

if TYPE_CHECKING:
    from agno.knowledge.document import Document
    from agno.knowledge.knowledge import Knowledge

# Relevance gate: empty result if the BEST candidate scores below this.
# Gates the query as a whole, not each document -- a per-document floor would
# silently demote hybrid search to vector-only, since hybrid's lexical half
# can rank a topically-correct hit at a low cosine. 0.26 was chosen by
# measuring end-to-end Planner decisions (not raw retrieval precision, which
# has no clean threshold on this corpus): it beat 0.32 on both recall and
# false-duplicate rate over 34 queries. Tied to `EMBEDDER_MODEL`; re-sweep with
# `benchmarks/recalibrate.py` (offline) and `benchmarks/judge.py` (end-to-end)
# after changing the embedder.
MIN_SIMILARITY = float(os.getenv("MIN_SIMILARITY", "0.26"))

# Chunks to pull before grouping collapses them to `num_documents` documents.
OVERFETCH = 4

MAX_CANDIDATES = 50  # ceiling on the over-fetch above


def cosine_similarity(left: list[float], right: list[float]) -> float:
    """Cosine similarity of two vectors, or 0.0 if either has no magnitude."""
    import numpy as np

    first = np.asarray(left, dtype=float)
    second = np.asarray(right, dtype=float)
    denominator = float(np.linalg.norm(first) * np.linalg.norm(second))
    if denominator == 0.0:
        return 0.0
    return float(first @ second / denominator)


def _document_key(document: Document) -> str:
    """Identity used when grouping chunks: post file stem, falling back to
    `content_id` then a content slice so unnamed chunks never merge."""
    return document.name or document.content_id or document.content[:120]


def _as_result(document: Document, similarity: float) -> dict[str, Any]:
    """One search hit, shaped for the model to read. `similarity` lets the
    Planner judge whether a close topic is really the same topic."""
    metadata = document.meta_data or {}
    result: dict[str, Any] = {
        "name": document.name,
        "similarity": round(similarity, 3),
        "content": document.content,
    }
    for field in ("file", "pilar", "pillar", "status", "data", "date", "tema"):
        if field in metadata:
            result[field] = metadata[field]
    return result


def search(
    knowledge: Knowledge,
    query: str,
    num_documents: int | None = None,
    min_similarity: float | None = None,
) -> list[dict[str, Any]]:
    """Search `knowledge`, drop the irrelevant, and return one hit per document.
    Empty list (rendered by Agno as "No documents found") when the query clears
    nothing. Result order is the vector db's own ranking, not re-ranked here."""
    from linkedin_growth.config import embedder

    limit = num_documents or knowledge.max_results
    threshold = MIN_SIMILARITY if min_similarity is None else min_similarity

    candidates = knowledge.search(
        query, max_results=min(limit * OVERFETCH, MAX_CANDIDATES)
    )
    if not candidates:
        return []

    query_embedding = embedder().get_embedding(query)
    if not query_embedding:
        # No embedding, no way to gate; ranked hits beat nothing.
        return _group_by_document(candidates, {}, limit)

    scores = {
        id(document): cosine_similarity(query_embedding, document.embedding)
        for document in candidates
        if document.embedding
    }
    if not scores or max(scores.values()) < threshold:
        return []

    return _group_by_document(candidates, scores, limit)


def _group_by_document(
    candidates: list[Document], scores: dict[int, float], limit: int
) -> list[dict[str, Any]]:
    """Collapse chunks to one hit per document. First occurrence wins, since
    candidates arrive best-first and re-sorting would undo that ranking."""
    seen: set[str] = set()
    results: list[dict[str, Any]] = []
    for document in candidates:
        key = _document_key(document)
        if key in seen:
            continue
        seen.add(key)
        results.append(_as_result(document, scores.get(id(document), 0.0)))
        if len(results) >= limit:
            break
    return results


def build_retriever(
    knowledge_factory: Callable[[], Knowledge],
    min_similarity: float | None = None,
) -> Callable[..., list[dict[str, Any]]]:
    """Wrap a knowledge factory into an Agno `knowledge_retriever`. Takes the
    factory, not the `Knowledge`, so nothing is built at import time. Accepts
    `query`/`num_documents` and swallows the rest, since Agno injects by name."""

    def retriever(
        query: str, num_documents: int | None = None, **_: Any
    ) -> list[dict[str, Any]]:
        return search(
            knowledge_factory(),
            query,
            num_documents=num_documents,
            min_similarity=min_similarity,
        )

    return retriever
