"""Module 5's improvement: keyword search next to the vectors, fused, then reranked."""

from doc_assistant import retrieve
from doc_assistant.context import Passage


def p(cid):
    return Passage(cid, "d", "k", "1", "T", "policy", "public", "2026-01-01", "", "s", "text")


def test_reciprocal_rank_fusion_worked_example():
    dense = [p("a"), p("b"), p("c")]
    words = [p("c"), p("d")]
    # a: 1/61 = 0.01639; b: 1/62 = 0.01613; c: 1/63 + 1/61 = 0.03227; d: 1/62 = 0.01613
    assert [x.chunk_id for x in retrieve.rrf(dense, words)] == ["c", "a", "b", "d"]


def test_small_common_words_are_not_keywords():
    assert retrieve.keywords("What is the warranty on the PW-2200?") == ["warranty", "pw-2200"]


def test_keyword_search_finds_an_exact_code(loaded):
    st = loaded.app.state
    with st.db.tenant("larkfield") as conn:
        rows = conn.execute(retrieve.KEYWORD, {"tenant": "larkfield", "access": ["public", "staff"],
                                               "as_of": "2026-10-11", "embedder": st.embedder.name,
                                               "words": retrieve.keywords("What is LB-1?"), "k": 3}).fetchall()
    assert rows and "LB-1" in rows[0]["text"]


def test_both_modes_return_top_k_of_one_shop(loaded):
    from dataclasses import replace

    from doc_assistant.rerank import WordOverlapReranker

    st = loaded.app.state
    with st.db.admin() as conn:
        bramble = {r["id"] for r in conn.execute(
            "SELECT document_id::text AS id FROM documents WHERE tenant_id = 'bramble'").fetchall()}
    for mode in ("dense", "hybrid_rerank"):
        s = replace(st.settings, retrieval_mode=mode)
        with st.db.tenant("bramble") as conn:
            found = retrieve.search(conn, "How much does the reading room cost on Saturday?", "bramble",
                                    ("public", "staff"), "2026-10-11", st.embedder, s, WordOverlapReranker())
        assert len(found) == 5 and {f.document_id for f in found} <= bramble
