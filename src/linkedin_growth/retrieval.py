"""The retriever the agents search through, instead of Agno's default.

Two problems with the raw `knowledge.search()` made this necessary, both found by
measuring rather than by reading:

**1. Search has no floor.** It returns the nearest neighbours, always. Asking the
posts base about "como fazer pao de queijo" returned both posts, with no signal
that neither is about anything of the sort. For the Planner, whose job is to
decide "have I written this already?", a hit on an unrelated post is a false
duplicate, and a false duplicate blocks a legitimate topic. Agno's `Document`
does not carry the score (`LanceDb._build_search_results` drops it), but it does
carry the chunk's `embedding`, so the similarity is recomputed here from data
already in hand, and used to gate the query. See `MIN_SIMILARITY` for why the
gate is on the query and not on each document.

**2. One document can fill every slot.** Chunking splits a post into several
rows, and each row competes separately. A search for "custo latencia" came back
with four chunks of one post and one of the other: `max_results=5` had been spent
on two documents. Grouping by document, keeping its highest-ranked chunk, makes
five results mean five posts.

Both are fixed in one place because Agno supports it directly: an agent's
`knowledge_retriever` replaces the default search behind the same
`search_knowledge_base` tool the model already calls, so no agent instruction has
to change.
"""

from __future__ import annotations

import os
from typing import TYPE_CHECKING, Any, Callable

if TYPE_CHECKING:
    from agno.knowledge.document import Document
    from agno.knowledge.knowledge import Knowledge

# The relevance gate: if the BEST candidate scores below this, the query is
# treated as being about nothing in the corpus and the search returns empty.
#
# It gates the query, not each document, and that distinction was measured rather
# than reasoned. Asking the posts base "por que minha conta da API triplicou"
# ranks the cost/latency post first, which is correct, on a cosine of only 0.228,
# because the lexical half of the hybrid search matched what the vector half
# missed. Filtering each document at 0.32 would have thrown that hit away and
# left the semantically-closer but topically-wrong post in its place. A per-
# document cosine floor silently demotes hybrid search to vector search.
#
# So: cosine decides whether the corpus has anything to say about the query at
# all, and the vector db's own ranking decides what comes back. One number for
# the floor, RRF for the order.
#
# The value was 0.32, chosen from a two-post corpus where relevant queries scored
# 0.41-0.57 and irrelevant ones 0.15-0.25 and the gap looked clean. It is 0.26
# now, and the reason is worth keeping because it is not what the first
# measurement predicted.
#
# On a 46-post archive the gap closes: answerable queries span 0.275-0.842 and
# unanswerable ones 0.155-0.746, with 18 of 20 answerable scoring below the worst
# unanswerable. **No threshold separates them.** Raising the gate to cut phantom
# hits cuts real ones at the same rate, so tuning this number for precision is
# not a trade worth making - it is not even a trade, just loss.
#
# What made 0.26 the answer was measuring the decision the gate actually feeds,
# with the model in the loop: the Planner reads the hits and judges, and it is
# much better at rejecting a lookalike than a cosine threshold is. Retrieval
# alone returned the near-duplicate trap in 87.5% of cases; the Planner rejected
# 7 of those 8 as new topics. So the gate should be tuned for RECALL and the
# judgement left to the model. Measured end to end over 34 queries:
#
#                    finds a written topic    rejects an unwritten one
#   0.32                     85.0%                    85.7%
#   0.26                     90.0%                    92.9%
#
# 0.26 wins on both, which is the part worth remembering: a tighter gate was
# hiding the context the model needed to judge with, so it lost recall AND made
# the false-duplicate rate worse.
#
# The number belongs to the embedder, not to the project. Changing
# `EMBEDDER_MODEL` invalidates it. `benchmarks/recalibrate.py` sweeps it offline
# for free; `benchmarks/judge.py` measures the end-to-end decision and costs
# about $0.45 a run.
MIN_SIMILARITY = float(os.getenv("MIN_SIMILARITY", "0.26"))

# How many chunks to pull before grouping. Grouping collapses several chunks into
# one result, so asking for exactly `num_documents` would routinely return fewer
# documents than requested.
OVERFETCH = 4

# A ceiling on the over-fetch, so a large `num_documents` cannot turn one search
# into a table scan.
MAX_CANDIDATES = 50


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
    """What counts as "the same document" when grouping.

    The name is the post's file stem, which is what the Planner reasons about.
    `content_id` is the fallback for a document Agno named differently, and the
    content itself is the last resort so two unnamed chunks never merge.
    """
    return document.name or document.content_id or document.content[:120]


def _as_result(document: Document, similarity: float) -> dict[str, Any]:
    """One search hit, shaped for the model to read.

    `similarity` is included on purpose. The Planner is told to judge whether a
    close topic is really the same topic, and it cannot do that if every hit
    arrives looking equally certain.
    """
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

    Returns an empty list when the query clears nothing, which Agno renders to the
    model as "No documents found". That is the whole point: silence is a truthful
    answer, and it is the answer the default search could never give.

    The order of what does come back is the vector db's, not a re-ranking. For the
    posts base that order is RRF over hybrid search, and preserving it is what
    keeps an exact-token match (a model name, a version, a number) ahead of a
    merely similar-sounding post.
    """
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
        # No embedding means no way to gate. Returning the ranked hits beats
        # returning nothing: the agent still gets what the vector db ranked.
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
    """Collapse chunks to one hit per document, keeping the incoming order.

    First occurrence wins, because the candidates arrive best-first: the chunk the
    vector db ranked highest is the one worth showing. Sorting by score here
    instead would override the ranking that `search` just went to the trouble of
    preserving.
    """
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
    """Wrap a knowledge factory into an Agno `knowledge_retriever`.

    Takes the factory rather than the `Knowledge` so nothing is constructed at
    import time: building a `Knowledge` creates its LanceDB table, and agents are
    built while `agentos.py` is still importing.

    Agno injects parameters by name, so the returned function deliberately
    accepts `query` and `num_documents` and swallows the rest.
    """

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
