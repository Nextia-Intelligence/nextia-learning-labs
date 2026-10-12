"""Questions and answers of a shop."""

from fastapi import APIRouter, Depends, Request

from . import limits
from .access import Principal
from .deps import principal
from .documents import is_uuid
from .errors import not_found
from .models import AskRequest
from .pipeline import Deps, ask

router = APIRouter(prefix="/v1/tenants/{tenant}")


@router.post("/answers")
def post_answer(body: AskRequest, request: Request, who: Principal = Depends(principal)):
    st = request.app.state
    deps = Deps(st.db, st.settings, st.embedder, st.provider, st.reranker)
    result = ask(deps, who, body.question.strip(), body.as_of.isoformat() if body.as_of else None)
    return {"answer": result.__dict__, "links": {"self": f"/v1/tenants/{who.tenant_id}/answers/{result.answer_id}"}}


ANSWER_COLUMNS = ("answer_id::text AS answer_id, user_id, question, as_of::text AS as_of, answerable, answer, citations,"
                  " checks, provider, model, input_tokens, output_tokens, cost_usd::float AS cost_usd, latency_ms,"
                  " trace_id, created_at")


@router.get("/answers")
def list_answers(request: Request, limit: int = 20, who: Principal = Depends(principal)):
    with request.app.state.db.tenant(who.tenant_id) as conn:
        rows = conn.execute(f"SELECT {ANSWER_COLUMNS} FROM answers WHERE tenant_id = %s AND user_id = %s"
                            " ORDER BY created_at DESC LIMIT %s", (who.tenant_id, who.user_id, min(limit, 100))).fetchall()
    return {"answers": rows}


@router.get("/answers/{answer_id}")
def get_answer(request: Request, answer_id: str, who: Principal = Depends(principal)):
    with request.app.state.db.tenant(who.tenant_id) as conn:
        row = conn.execute(f"SELECT {ANSWER_COLUMNS} FROM answers WHERE tenant_id = %s AND answer_id = %s::uuid"
                           " AND user_id = %s", (who.tenant_id, answer_id, who.user_id)).fetchone() \
            if is_uuid(answer_id) else None
    if row is None:
        raise not_found()
    return {"answer": row}


@router.get("/usage")
def get_usage(request: Request, who: Principal = Depends(principal)):
    with request.app.state.db.tenant(who.tenant_id) as conn:
        return {"tenant": who.tenant_id, **limits.usage(conn, who.tenant_id, request.app.state.settings.today_date(),
                                                         request.app.state.settings)}
