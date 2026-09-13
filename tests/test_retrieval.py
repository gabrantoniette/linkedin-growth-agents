"""The retriever that sits between the agents and the vector database.

Two behaviours are worth locking down, because both were regressions found by
measuring a live index rather than by reading the code, and both are the kind
that fail silently:

1. An off-topic query has to come back **empty**. Vector search always returns
   its nearest neighbours, so without a gate the Planner reads a hit on an
   unrelated post as a duplicate and refuses a legitimate topic.

2. The vector database's ranking has to **survive**. The posts base is hybrid,
   and its lexical half is the only thing that keeps "Opus 5" apart from
   "Sonnet 5". Re-sorting the results by cosine would quietly turn hybrid search
   back into vector search, which is the whole reason the base is hybrid.

No embedder and no LanceDB here. The retriever's logic is pure given a search
result, so the tests hand it fake documents with hand-written vectors: that keeps
them fast, offline, and independent of which embedding model is configured.
"""

from __future__ import annotations

import pytest

from linkedin_growth import retrieval
from linkedin_growth.retrieval import cosine_similarity, search


# ==============================================================================
# Doubles
# ==============================================================================


class FakeDocument:
    """The parts of `agno.knowledge.document.Document` the retriever touches."""

    def __init__(self, name, embedding, content="conteudo", meta_data=None):
        self.name = name
        self.embedding = embedding
        self.content = content
        self.content_id = name
        self.meta_data = meta_data or {}


class FakeKnowledge:
    """A knowledge base that returns a fixed list, in a fixed order.

    The order is the point: it stands in for the vector db's ranking, which the
    retriever must not reorder.
    """

    max_results = 5

    def __init__(self, documents):
        self.documents = documents
        self.calls: list[tuple[str, int]] = []

    def search(self, query, max_results=None, **kwargs):
        self.calls.append((query, max_results))
        return list(self.documents)


@pytest.fixture
def fixed_query_embedding(monkeypatch):
    """Pin the query vector to [1, 0], so a document's vector sets its score.

    A document at [1, 0] scores 1.0, one at [0, 1] scores 0.0, and one at
    [1, 1] scores about 0.707. That makes every expectation below arithmetic
    instead of a guess about what some model happens to embed.
    """

    class StubEmbedder:
        def get_embedding(self, text):
            return [1.0, 0.0]

    monkeypatch.setattr(
        "linkedin_growth.config.embedder", lambda: StubEmbedder()
    )


# ==============================================================================
# Cosine similarity
# ==============================================================================


@pytest.mark.parametrize(
    "left,right,expected",
    [
        ([1.0, 0.0], [1.0, 0.0], 1.0),
        ([1.0, 0.0], [0.0, 1.0], 0.0),
        ([1.0, 0.0], [-1.0, 0.0], -1.0),
        # Magnitude must not matter, only direction.
        ([1.0, 0.0], [5.0, 0.0], 1.0),
    ],
)
def test_cosine_similarity(left, right, expected):
    assert cosine_similarity(left, right) == pytest.approx(expected)


def test_cosine_similarity_of_zero_vector_is_zero():
    """A zero vector has no direction, and dividing by its norm would raise."""
    assert cosine_similarity([0.0, 0.0], [1.0, 0.0]) == 0.0


# ==============================================================================
# The relevance gate
# ==============================================================================


def test_off_topic_query_returns_nothing(fixed_query_embedding):
    """The failure this whole module exists to prevent.

    Every candidate is orthogonal to the query, so the corpus has nothing to say
    and the honest answer is an empty list. Agno renders that to the model as
    "No documents found".
    """
    knowledge = FakeKnowledge(
        [
            FakeDocument("post-a", [0.0, 1.0]),
            FakeDocument("post-b", [0.0, 1.0]),
        ]
    )

    assert search(knowledge, "pao de queijo") == []


def test_relevant_query_returns_hits(fixed_query_embedding):
    knowledge = FakeKnowledge([FakeDocument("post-a", [1.0, 0.0])])

    results = search(knowledge, "on topic")

    assert [hit["name"] for hit in results] == ["post-a"]
    assert results[0]["similarity"] == pytest.approx(1.0)


def test_gate_is_on_the_query_not_on_each_document(fixed_query_embedding):
    """A low-scoring document still comes back when the query itself is on topic.

    This is the regression that matters most. On the real index, the hybrid search
    ranked the right post FIRST on a cosine of only 0.228, because the lexical half
    matched what the vector half missed. Filtering document by document would have
    dropped exactly that hit. So once any candidate clears the gate, the whole
    ranked list comes back.
    """
    knowledge = FakeKnowledge(
        [
            # Ranked first by the vector db, but semantically distant.
            FakeDocument("lexical-match", [0.05, 1.0]),
            FakeDocument("semantic-match", [1.0, 0.0]),
        ]
    )

    results = search(knowledge, "on topic")

    assert [hit["name"] for hit in results] == ["lexical-match", "semantic-match"]


def test_threshold_can_be_overridden(fixed_query_embedding):
    """The caller can tighten or loosen the gate without touching the module."""
    knowledge = FakeKnowledge([FakeDocument("post-a", [1.0, 1.0])])  # ~0.707

    assert search(knowledge, "q", min_similarity=0.9) == []
    assert len(search(knowledge, "q", min_similarity=0.5)) == 1


def test_default_threshold_comes_from_the_module(monkeypatch, fixed_query_embedding):
    """`MIN_SIMILARITY` is the default, so tuning it changes every agent at once."""
    monkeypatch.setattr(retrieval, "MIN_SIMILARITY", 0.9)
    knowledge = FakeKnowledge([FakeDocument("post-a", [1.0, 1.0])])  # ~0.707

    assert search(knowledge, "q") == []


# ==============================================================================
# Ranking and grouping
# ==============================================================================


def test_ranking_order_is_preserved(fixed_query_embedding):
    """The retriever must not re-sort. The vector db already ranked these."""
    knowledge = FakeKnowledge(
        [
            FakeDocument("third-best-semantically", [1.0, 0.0]),
            FakeDocument("but-ranked-second", [1.0, 1.0]),
            FakeDocument("and-ranked-third", [1.0, 2.0]),
        ]
    )

    results = search(knowledge, "q")

    assert [hit["name"] for hit in results] == [
        "third-best-semantically",
        "but-ranked-second",
        "and-ranked-third",
    ]


def test_chunks_of_one_document_collapse_to_one_hit(fixed_query_embedding):
    """Five results have to mean five documents, not five chunks of two.

    On the real index a search returned four chunks of one post and one of
    another: `max_results=5` had been spent on two documents.
    """
    knowledge = FakeKnowledge(
        [
            FakeDocument("post-a", [1.0, 0.0], content="chunk 1"),
            FakeDocument("post-a", [1.0, 0.0], content="chunk 2"),
            FakeDocument("post-a", [1.0, 0.0], content="chunk 3"),
            FakeDocument("post-b", [1.0, 0.0], content="only chunk"),
        ]
    )

    results = search(knowledge, "q")

    assert [hit["name"] for hit in results] == ["post-a", "post-b"]
    # The highest-ranked chunk is the one kept, not the last one seen.
    assert results[0]["content"] == "chunk 1"


def test_limit_counts_documents_not_chunks(fixed_query_embedding):
    knowledge = FakeKnowledge(
        [
            FakeDocument("post-a", [1.0, 0.0], content="chunk 1"),
            FakeDocument("post-a", [1.0, 0.0], content="chunk 2"),
            FakeDocument("post-b", [1.0, 0.0]),
            FakeDocument("post-c", [1.0, 0.0]),
        ]
    )

    results = search(knowledge, "q", num_documents=2)

    assert [hit["name"] for hit in results] == ["post-a", "post-b"]


def test_candidates_are_overfetched_so_grouping_can_still_fill_the_limit(
    fixed_query_embedding,
):
    """Grouping shrinks the list, so the search has to ask for more than it needs."""
    knowledge = FakeKnowledge([FakeDocument("post-a", [1.0, 0.0])])

    search(knowledge, "q", num_documents=5)

    _, requested = knowledge.calls[0]
    assert requested == 5 * retrieval.OVERFETCH


def test_overfetch_is_capped(fixed_query_embedding):
    """A large limit must not turn one search into a table scan."""
    knowledge = FakeKnowledge([FakeDocument("post-a", [1.0, 0.0])])

    search(knowledge, "q", num_documents=1000)

    _, requested = knowledge.calls[0]
    assert requested == retrieval.MAX_CANDIDATES


# ==============================================================================
# What the model receives
# ==============================================================================


def test_metadata_the_planner_needs_is_carried_through(fixed_query_embedding):
    """`status: reprovado` means "rewrite this", not "avoid this topic".

    The Planner is instructed to tell those apart, which it can only do if the
    front matter survives the trip.
    """
    knowledge = FakeKnowledge(
        [
            FakeDocument(
                "post-a",
                [1.0, 0.0],
                meta_data={
                    "file": "posts/2026-09-04-a.md",
                    "pilar": "Entendi",
                    "status": "reprovado",
                    "ruido": "nao deve aparecer",
                },
            )
        ]
    )

    hit = search(knowledge, "q")[0]

    assert hit["file"] == "posts/2026-09-04-a.md"
    assert hit["pilar"] == "Entendi"
    assert hit["status"] == "reprovado"
    assert "ruido" not in hit


def test_similarity_is_reported(fixed_query_embedding):
    """The Planner has to weigh "close" against "the same", so it needs the number."""
    knowledge = FakeKnowledge([FakeDocument("post-a", [1.0, 1.0])])

    hit = search(knowledge, "q", min_similarity=0.1)[0]

    assert hit["similarity"] == pytest.approx(0.707, abs=0.001)


# ==============================================================================
# Degradation
# ==============================================================================


def test_empty_search_result_returns_empty(fixed_query_embedding):
    assert search(FakeKnowledge([]), "q") == []


def test_documents_without_embeddings_do_not_crash_the_gate(fixed_query_embedding):
    """An unvectorized row must not take the whole search down."""
    knowledge = FakeKnowledge(
        [
            FakeDocument("no-vector", None),
            FakeDocument("post-a", [1.0, 0.0]),
        ]
    )

    results = search(knowledge, "q")

    assert "post-a" in [hit["name"] for hit in results]


def test_all_documents_without_embeddings_returns_empty(fixed_query_embedding):
    """Nothing to score means nothing can clear the gate."""
    knowledge = FakeKnowledge([FakeDocument("no-vector", None)])

    assert search(knowledge, "q") == []


def test_unembeddable_query_falls_back_to_the_ranking(monkeypatch):
    """If the query cannot be embedded, return what was ranked rather than nothing.

    Losing the gate degrades the results. Returning an empty list would tell the
    Planner the topic is new, which is a worse answer than an unfiltered one.
    """

    class BrokenEmbedder:
        def get_embedding(self, text):
            return []

    monkeypatch.setattr(
        "linkedin_growth.config.embedder", lambda: BrokenEmbedder()
    )
    knowledge = FakeKnowledge(
        [
            FakeDocument("post-a", [0.0, 1.0]),
            FakeDocument("post-a", [0.0, 1.0]),
            FakeDocument("post-b", [0.0, 1.0]),
        ]
    )

    results = search(knowledge, "q")

    # Still grouped, still ranked, just ungated.
    assert [hit["name"] for hit in results] == ["post-a", "post-b"]


# ==============================================================================
# Wiring
# ==============================================================================


def test_build_retriever_does_not_build_the_knowledge_base(fixed_query_embedding):
    """The factory must stay uncalled until a run needs it.

    Constructing a `Knowledge` creates its LanceDB table, and agents are built
    while `agentos.py` is still importing. `config.py` keeps that import free of
    disk writes and this is what holds the line.
    """
    built = []

    def factory():
        built.append(True)
        return FakeKnowledge([FakeDocument("post-a", [1.0, 0.0])])

    retriever = retrieval.build_retriever(factory)
    assert built == []

    retriever(query="q", num_documents=3)
    assert built == [True]


def test_retriever_tolerates_the_extra_kwargs_agno_injects(fixed_query_embedding):
    """Agno injects by signature and can pass more than the retriever asked for."""
    retriever = retrieval.build_retriever(
        lambda: FakeKnowledge([FakeDocument("post-a", [1.0, 0.0])])
    )

    results = retriever(query="q", num_documents=1, filters=None, user_id="user")

    assert [hit["name"] for hit in results] == ["post-a"]


def test_the_two_agents_use_the_retriever(no_api):
    """A retriever nothing is wired to is dead code.

    The Planner and the Writer are the two that search: the Planner to avoid
    repeating a topic, the Writer to match the user's voice.

    `no_api` is what makes this runnable without a key. Building an agent calls
    `config.model()`, which calls `require_anthropic()`, so without the fixture
    this test passes only on a machine that has a real key in `.env` - and fails
    in CI, which has neither the file nor the secret. The fixture swaps in the
    spy model, which is also what keeps the test from ever reaching the network.
    """
    from linkedin_growth import agents

    by_name = {agent.name: agent for agent in agents.all_agents()}

    for name in ("Editorial Planner", "Writer"):
        assert by_name[name].knowledge_retriever is not None, name
