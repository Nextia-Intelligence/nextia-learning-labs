"""The vertical slice: retrieval with filters, the answer, its checks, the stored row and the trace."""

import json

from doc_assistant import tracing
from doc_assistant.pipeline import NO_PASSAGES, Deps, ask
from scripts.common import as_member


def deps_of(client) -> Deps:
    st = client.app.state
    return Deps(st.db, st.settings, st.embedder, st.provider, st.reranker)


def test_the_date_picks_the_version_in_force(loaded):
    d = deps_of(loaded)
    who = as_member(d, "usr-ines", "bramble")
    now = ask(d, who, "Returning a book without a receipt: store credit?", "2026-10-11")
    later = ask(d, who, "Returning a book without a receipt: store credit?", "2026-12-10")
    versions_now = {(p["doc_key"], p["version"]) for p in now.passages if p["doc_key"] == "returns-policy"}
    versions_later = {(p["doc_key"], p["version"]) for p in later.passages if p["doc_key"] == "returns-policy"}
    assert versions_now == {("returns-policy", "1")} and versions_later == {("returns-policy", "2")}


def test_only_the_callers_shop_is_searched(loaded):
    d = deps_of(loaded)
    result = ask(d, as_member(d, "usr-ines", "bramble"), "What is the warranty on the PW-2200 pressure washer?")
    with d.db.admin() as conn:
        bramble_docs = {r["document_id"] for r in conn.execute(
            "SELECT document_id::text FROM documents WHERE tenant_id = 'bramble'").fetchall()}
    assert result.passages and {p["document_id"] for p in result.passages} <= bramble_docs


def test_no_passage_means_no_model_call(loaded):
    d = deps_of(loaded)
    with d.db.admin() as conn:
        conn.execute("UPDATE documents SET status = 'failed' WHERE tenant_id = 'bramble'")
    result = ask(d, as_member(d, "usr-ines", "bramble"), "How long is a gift card valid?")
    assert result.answer == NO_PASSAGES and result.provider == "none" and not result.answerable


def test_the_answer_is_stored_with_its_evidence_and_cost(loaded):
    d = deps_of(loaded)
    result = ask(d, as_member(d, "usr-ines", "bramble"), "How long is a gift card valid?")
    with d.db.tenant("bramble") as conn:
        row = conn.execute("SELECT * FROM answers WHERE answer_id = %s", (result.answer_id,)).fetchone()
    assert row["user_id"] == "usr-ines" and row["provider"] == "mock" and len(row["cited_documents"]) == 1
    assert row["checks"]["passages"] == [p["chunk_id"] for p in result.passages]


def test_every_question_has_a_trace_with_its_steps(loaded, tmp_path):
    from opentelemetry import trace
    from opentelemetry.sdk.trace.export import SimpleSpanProcessor

    tracing.setup("", "test")
    path = tmp_path / "spans.jsonl"
    trace.get_tracer_provider().add_span_processor(SimpleSpanProcessor(tracing.JsonLinesExporter(str(path))))
    d = deps_of(loaded)
    result = ask(d, as_member(d, "usr-ines", "bramble"), "How long is a gift card valid?")
    spans = [json.loads(x) for x in path.read_text().splitlines() if json.loads(x)["trace_id"] == result.trace_id]
    assert {s["name"] for s in spans} == {"ask", "retrieve", "generate", "check", "store"}
    assert "How long" not in path.read_text()   # the trace never holds the question's text
