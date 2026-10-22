"""The month's estate report, and finding unregistered AI."""

from conftest import PROJECT, stream
from estate import clock, discovery, report

TRIAGE = dict(stream("ticket-triage")[0]["body"], model="fast-small")


def some_traffic(estate, gateway, n=3):
    c = gateway()
    for _ in range(n):
        c.post("/v1/chat/completions", json=TRIAGE, headers={"authorization": f"Bearer {estate.token('ticket-triage')}"})
    c.post("/v1/chat/completions", json=dict(TRIAGE, model="strong-reasoning"),
           headers={"authorization": f"Bearer {estate.token('ticket-triage')}"})


def test_the_monthly_report_answers_the_boards_questions(estate, gateway):
    some_traffic(estate, gateway)
    month = clock.now().strftime("%Y-%m")
    text = report.monthly(month)
    for heading in ("## 1. Inventory", "## 2. Risk tiers", "## 3. Spending", "## 4. What the controls stopped",
                    "## 5. Exceptions and incidents", "## 6. Reviews and owners", "## 7. What this evidence cannot answer"):
        assert heading in text
    assert "| capability | 1 |" in text                      # the refused strong-reasoning call
    assert "release-judge: review overdue" in text


def test_a_bill_line_that_is_not_the_gateways_is_a_finding(tmp_path):
    bill = tmp_path / "azure-bill.csv"
    bill.write_text("month,provider,key_id,deployment,requests,tokens_in,tokens_out,cost_usd\n"
                    "2026-09,azure,az-key-9,chat-small,1000,1,1,1.0\n2026-09,azure,az-key-3,chat-strong,12,1,1,0.4\n"
                    "2026-09,fernway,fw-7Q2K,fernway-swift,4,1,1,0.01\n")
    found = discovery.from_bill(bill, discovery.inventory())
    assert [f["key_id"] for f in found] == ["az-key-3", "fw-7Q2K"]
    assert found[0]["finding"] == "a key that nobody told the platform about"
    assert found[1]["finding"].startswith("a provider without a contract (fernway)")


def test_a_direct_connection_in_the_egress_log_is_a_finding(tmp_path):
    log = tmp_path / "egress.csv"
    log.write_text("time,source_host,destination,provider,key_id,status,bytes_out\n"
                   "2026-09-07T06:00:00,build-runner-3,api.fernway.example,fernway,fw-7Q2K,200,11233\n"
                   "2026-09-07T06:00:01,gateway-a,larkfield-ai.openai.azure.example,azure,az-key-9,200,7435\n")
    found = discovery.from_egress(log, discovery.inventory())
    assert len(found) == 1 and found[0]["host"] == "build-runner-3"


def test_the_digest_scripts_key_and_address_are_found_in_code():
    found = discovery.from_code(PROJECT / "apps" / "digest")
    kinds = {f["finding"] for f in found}
    assert "practice provider key in code" in kinds and "model provider address in code" in kinds
    assert all("7Q2K9XW4" not in f["evidence"] for f in found)          # a key is never printed whole
