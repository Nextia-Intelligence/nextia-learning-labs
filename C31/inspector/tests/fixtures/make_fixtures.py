"""Write the live-mode test answers (Tempo and Prometheus) from the saved week. Run once; the files are committed.

Tempo's real answers were NOT recorded here (no Tempo on the authoring computer). These files follow the shapes of
Tempo's HTTP API: /api/search -> {"traces": [{"traceID": ...}]} (hex, leading zeros dropped), and /api/traces/<id> ->
{"batches": [...]} with base64 IDs, numeric span kinds and status codes, and "instrumentationLibrarySpans" in one
trace (the older shape), "scopeSpans" in the others.
"""

import base64
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent.parent))
from larkfield_inspector.vendor.obs.model import lines  # noqa: E402

RUNS = ["R-1014-040", "R-1012-034", "R-1018-010"]
KIND = {"SPAN_KIND_INTERNAL": 1, "SPAN_KIND_SERVER": 2, "SPAN_KIND_CLIENT": 3}
CODE = {"STATUS_CODE_UNSET": 0, "STATUS_CODE_OK": 1, "STATUS_CODE_ERROR": 2}


def b64(hexid: str) -> str:
    return base64.b64encode(bytes.fromhex(hexid)).decode() if hexid else ""


def main():
    data = HERE.parent.parent / "larkfield_inspector" / "data" / "week"
    traces: dict[str, list] = {}
    run_traces: dict[str, set] = {}
    for req in lines(data / "traces.jsonl"):
        for rs in req["resourceSpans"]:
            for ss in rs["scopeSpans"]:
                for s in ss["spans"]:
                    attrs = {a["key"]: a["value"] for a in s.get("attributes", [])}
                    rid = attrs.get("larkfield.run.id", {}).get("stringValue")
                    if rid in RUNS:
                        run_traces.setdefault(rid, set()).add(s["traceId"])
                    traces.setdefault(s["traceId"], []).append((rs["resource"], ss["scope"], s))
    wanted = sorted({t for r in RUNS for t in run_traces[r]})
    search = {"traces": [{"traceID": t.lstrip("0"), "rootServiceName": "support-workflow"} for t in wanted],
              "metrics": {"inspectedTraces": len(wanted)}}
    (HERE / "tempo_search.json").write_text(json.dumps(search, indent=1))
    for n, t in enumerate(wanted):
        resource = traces[t][0][0]
        spans = []
        for _, scope, s in traces[t]:
            s = dict(s)
            s["traceId"], s["spanId"] = b64(s["traceId"]), b64(s["spanId"])
            if s.get("parentSpanId"):
                s["parentSpanId"] = b64(s["parentSpanId"])
            s["kind"] = KIND.get(s.get("kind"), 1)
            if "status" in s:
                s["status"] = {**s["status"], "code": CODE.get(s["status"].get("code"), 0)}
            s["links"] = [{**link, "traceId": b64(link["traceId"]), "spanId": b64(link["spanId"])} for link in s.get("links", [])]
            spans.append(s)
        key = "instrumentationLibrarySpans" if n == 0 else "scopeSpans"
        doc = {"batches": [{"resource": resource, key: [{"scope": traces[t][0][1], "spans": spans}]}]}
        (HERE / f"tempo_trace_{t}.json").write_text(json.dumps(doc, indent=1))
    prom = {"status": "success", "data": {"resultType": "matrix", "result": [
        {"metric": {}, "values": [[1792036800, "0.0123"], [1792040400, "0.0050"]]}]}}
    (HERE / "prometheus_query_range.json").write_text(json.dumps(prom, indent=1))
    print(f"{len(wanted)} traces for {', '.join(RUNS)}")


if __name__ == "__main__":
    main()
