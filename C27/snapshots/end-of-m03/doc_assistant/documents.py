"""The documents of a shop: upload, list and status."""

import uuid

from fastapi import APIRouter, Depends, File, Form, Request, Response, UploadFile

from .access import Principal
from .deps import principal
from .errors import not_found
from .ingest import DOC_COLUMNS, create_document

router = APIRouter(prefix="/v1/tenants/{tenant}")


def is_uuid(value: str) -> bool:
    try:
        uuid.UUID(value)
        return True
    except ValueError:
        return False


def doc_out(row: dict, tenant: str) -> dict:
    return {**{k: (v.isoformat() if hasattr(v, "isoformat") else v) for k, v in row.items()},
            "links": {"self": f"/v1/tenants/{tenant}/documents/{row['document_id']}"}}


@router.post("/documents", status_code=202)
async def upload(request: Request, response: Response, file: UploadFile = File(...), doc_key: str = Form(""),
                 version: str = Form(""), title: str = Form(""), access: str = Form(""),
                 effective_from: str = Form(""), effective_to: str = Form(""), doc_type: str = Form(""),
                 who: Principal = Depends(principal)):
    s = request.app.state.settings
    data = await file.read(s.max_upload_bytes + 1)
    form = {"doc_key": doc_key, "version": version, "title": title, "access": access, "doc_type": doc_type,
            "effective_from": effective_from, "effective_to": effective_to}
    with request.app.state.db.tenant(who.tenant_id) as conn:
        row, duplicate = create_document(conn, who.tenant_id, who.user_id, file.filename or "upload", file.content_type,
                                         data, form, s)
    if duplicate:
        response.status_code = 200
    else:
        response.headers["Location"] = f"/v1/tenants/{who.tenant_id}/documents/{row['document_id']}"
    return {"document": doc_out(row, who.tenant_id), "duplicate": duplicate}


@router.get("/documents")
def list_documents(request: Request, who: Principal = Depends(principal)):
    with request.app.state.db.tenant(who.tenant_id) as conn:
        rows = conn.execute(f"SELECT {DOC_COLUMNS} FROM documents WHERE tenant_id = %s AND access = ANY(%s)"
                            " ORDER BY doc_key, version", (who.tenant_id, list(who.access_levels))).fetchall()
    counts: dict[str, int] = {}
    for r in rows:
        counts[r["status"]] = counts.get(r["status"], 0) + 1
    return {"tenant": who.tenant_id, "shop": who.shop, "role": who.role, "counts": counts,
            "documents": [doc_out(r, who.tenant_id) for r in rows]}


def _document(conn, who: Principal, document_id: str) -> dict:
    if not is_uuid(document_id):
        raise not_found()   # not even an ID: the same answer as a missing document
    row = conn.execute(f"SELECT {DOC_COLUMNS} FROM documents WHERE tenant_id = %s AND document_id = %s::uuid"
                       " AND access = ANY(%s)", (who.tenant_id, document_id, list(who.access_levels))).fetchone()
    if row is None:
        raise not_found()
    return row


@router.get("/documents/{document_id}")
def get_document(request: Request, document_id: str, who: Principal = Depends(principal)):
    with request.app.state.db.tenant(who.tenant_id) as conn:
        return {"document": doc_out(_document(conn, who, document_id), who.tenant_id)}

