"""The answer's schema, the citation checks and the providers, without a database."""

import json

import pytest

from doc_assistant.answer import AnswerProblem, build_request, parse_answer
from doc_assistant.cite import check_answer
from doc_assistant.context import Context, Passage, assemble
from doc_assistant.providers import Completion, LiveProvider, MockProvider, ProviderError, RecordedProvider, replay_key


def passage(cid="aaaaaaaaaaaa", text="Gift cards\nHow long they last\nA gift card is valid for 3 years.", **kw):
    base = dict(chunk_id=cid, document_id="d1", doc_key="gift-cards", version="1", title="Gift cards",
                doc_type="policy", access="public", effective_from="2026-09-15", effective_to="",
                section="How long they last", text=text)
    return Passage(**{**base, **kw})


def completion(data, **kw) -> Completion:
    return Completion(json.dumps(data) if not isinstance(data, str) else data, kw.get("finish", "stop"),
                      kw.get("refusal"), "chat-small", "test")


def test_request_has_the_shop_the_date_and_the_passages():
    ctx = assemble([passage()])
    req = build_request("How long is a gift card valid?", "2026-10-11", ctx, "chat-small", "Bramble Books")
    assert "staff of Bramble Books" in req["messages"][0]["content"]
    assert req["messages"][1]["content"].startswith("Question date: 2026-10-11\nQuestion: How long")
    header = "[aaaaaaaaaaaa] Gift cards | policy, version 1, in force from 2026-09-15, no end date"
    assert header in req["messages"][1]["content"]
    assert req["response_format"]["json_schema"]["strict"] is True


@pytest.mark.parametrize("c, problem", [
    (completion("not json"), "not a valid answer"),
    (completion({"answerable": True}), "not a valid answer"),
    (completion({"answerable": True, "answer": "x", "claims": []}, finish="length"), "cut"),
    (completion({}, refusal="I cannot help"), "refused"),
])
def test_unusable_answers_are_refused(c, problem):
    with pytest.raises(AnswerProblem, match=problem):
        parse_answer(c)


def test_citation_checks_constructed_cases():
    p = passage()
    known = {p.chunk_id: p}
    answer = parse_answer(completion({"answerable": True, "answer": "3 years.", "claims": [
        {"text": "A gift card is valid for 3 years.", "chunk_ids": ["aaaaaaaaaaaa"]},          # fine
        {"text": "A gift card is valid for 5 years.", "chunk_ids": ["aaaaaaaaaaaa"]},          # wrong number
        {"text": "A gift card is valid for 3 years.", "chunk_ids": ["000000000000"]},          # made-up ID
        {"text": "Gift cards can be refunded in cash.", "chunk_ids": []},                      # no citation
    ]}))
    checks = check_answer(answer, known, ["aaaaaaaaaaaa"], "How long? 2026-10-11")
    assert [c.problems for c in checks] == [[], ["number_not_found:5"], ["missing_id:000000000000"], ["no_citation"]]


def test_near_duplicates_of_other_documents_are_dropped_but_versions_are_kept():
    a = passage("a" * 12)
    twin = passage("b" * 12, document_id="d2", doc_key="faq")
    v2 = passage("c" * 12, document_id="d3", version="2")
    ctx = assemble([a, twin, v2])
    assert ctx.ids == ["a" * 12, "c" * 12] and ctx.dropped == [("b" * 12, "near-duplicate of " + "a" * 12)]


def test_the_mock_cites_its_first_passage_and_abstains_without_passages():
    req = build_request("q?", "2026-10-11", assemble([passage()]), "chat-small", "Bramble Books")
    data = json.loads(MockProvider().complete(req).text)
    assert data == {"answerable": True, "answer": "A gift card is valid for 3 years.",
                    "claims": [{"text": "A gift card is valid for 3 years.", "chunk_ids": ["aaaaaaaaaaaa"]}]}
    empty = build_request("q?", "2026-10-11", Context(), "chat-small", "Bramble Books")
    assert json.loads(MockProvider().complete(empty).text)["answerable"] is False


def test_recorded_replay_ignores_the_passages_and_says_when_they_differ(tmp_path):
    recorded = build_request("How long is a gift card valid?", "2026-10-11", assemble([passage()]), "chat-small",
                             "Bramble Books")
    response = {"choices": [{"message": {"content": json.dumps({"answerable": True, "answer": "3 years.", "claims": [
        {"text": "3 years.", "chunk_ids": ["aaaaaaaaaaaa"]}]})}, "finish_reason": "stop"}],
                "usage": {"prompt_tokens": 500, "completion_tokens": 50}}
    entry = {"request": recorded, "response": response, "latency_s": 1.2}
    (tmp_path / "answers.jsonl").write_text(json.dumps(entry) + "\n")
    rec = RecordedProvider(tmp_path)
    same = rec.complete(recorded)
    assert same.provider == "recorded" and same.note == "" and same.cost_usd == pytest.approx(0.000075)
    other = build_request("How long is a gift card valid?", "2026-10-11",
                          assemble([passage("bbbbbbbbbbbb", document_id="d9", doc_key="x", text="Other\nOther text."),
                                    passage()]), "chat-small", "Bramble Books")
    assert replay_key(other) == replay_key(recorded)
    replayed = rec.complete(other)
    assert replayed.provider == "recorded"
    assert "Recorded with passages aaaaaaaaaaaa; yours: bbbbbbbbbbbb, aaaaaaaaaaaa" in replayed.note
    # the recorded answer cites a passage that this search did not find: never shown
    without = build_request("How long is a gift card valid?", "2026-10-11", assemble([passage("bbbbbbbbbbbb")]),
                            "chat-small", "Bramble Books")
    c = rec.complete(without)
    assert c.provider == "mock" and "did not find" in c.note
    unknown = build_request("Another question?", "2026-10-11", assemble([passage()]), "chat-small", "Bramble Books")
    c = rec.complete(unknown)
    assert c.provider == "mock" and c.note.startswith("No recording for this question")


class SlowClient:
    """Stands in for the OpenAI client: always times out."""

    def __init__(self):
        self.calls = 0
        self.chat = self
        self.completions = self

    def create(self, **request):
        import httpx
        import openai

        self.calls += 1
        raise openai.APITimeoutError(request=httpx.Request("POST", "http://x"))


def test_a_timeout_is_one_clear_error():
    p = LiveProvider("http://127.0.0.1:9/v1", "", timeout_s=1)
    p.client = SlowClient()
    with pytest.raises(ProviderError) as e:
        p.complete({"model": "chat-small"})
    assert e.value.kind == "timeout" and p.client.calls == 1
