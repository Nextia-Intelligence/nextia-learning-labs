"""Upload a document and index it, as a job with visible states:

    uploaded -> parsing -> indexed
                        -> failed (with a message a person can act on)

`create_document` runs during the upload request: it checks the file, reads its metadata (front
matter, HTML <meta> tags or the PDF's Keywords; form fields win), saves the bytes and the row, and
returns at once (202). The worker (worker.py) does the slow part later: parse, chunk, embed.

Duplicate-safe (Module 4): the same bytes uploaded again by the same shop return the existing
document (200, "duplicate": true) instead of a second copy. Two shops may upload the same file.
"""

import hashlib
import io
import re
from datetime import date

import psycopg

from .errors import ApiError
from .parse import SUFFIXES, read_markdown

FIELDS = ("doc_key", "version", "title", "doc_type", "language", "access", "effective_from", "effective_to")
DOC_COLUMNS = ("document_id::text AS document_id, doc_key, version, title, doc_type, language, access,"
               " effective_from::text AS effective_from, coalesce(effective_to::text, '') AS effective_to,"
               " file_name, size_bytes, sha256, status, error, attempts, chunk_count,"
               " uploaded_by, uploaded_at, indexed_at")


def slug(text: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")[:60] or "document"


def embedded_metadata(name: str, data: bytes) -> dict:
    """The metadata a file carries itself. Never fails: a file that cannot be read gives {}
    here, and the worker reports the real problem when it parses the file."""
    try:
        if name.endswith((".md", ".txt")):
            return read_markdown(data.decode("utf-8-sig"))[0]
        if name.endswith((".html", ".htm")):
            text = data.decode("utf-8-sig")
            meta = dict(re.findall(r'<meta name="([a-z_]+)" content="([^"]*)"', text))
            h1 = re.search(r"<h1[^>]*>(.*?)</h1>", text, re.S)
            if h1 and "title" not in meta:
                meta["title"] = re.sub(r"<[^>]+>", "", h1[1]).strip()
            return meta
        if name.endswith(".pdf"):
            from pypdf import PdfReader

            info = PdfReader(io.BytesIO(data)).metadata or {}
            meta = dict(p.split("=", 1) for p in str(info.get("/Keywords", "")).split("; ") if "=" in p)
            if info.get("/Title") and "title" not in meta:
                meta["title"] = str(info["/Title"])
            return meta
    except Exception:  # noqa: BLE001 - a broken file is the worker's to report
        return {}
    return {}


def metadata(name: str, data: bytes, form: dict, today: str) -> dict:
    stem = re.sub(r"(\.v\d+)?\.[a-z]+$", "", name.lower())
    meta = {"doc_key": slug(stem), "version": "1", "title": stem.replace("-", " ").capitalize(),
            "doc_type": "policy", "language": "en", "access": "staff", "effective_from": today, "effective_to": ""}
    file_meta = embedded_metadata(name.lower(), data)
    if "doc_id" in file_meta:
        file_meta["doc_key"] = file_meta.pop("doc_id")
    meta.update({k: v for k, v in file_meta.items() if k in FIELDS and v is not None})
    meta.update({k: v for k, v in form.items() if k in FIELDS and v not in (None, "")})
    problems = []
    if meta["access"] not in ("public", "staff"):
        problems.append({"field": "access", "problem": "must be public or staff"})
    for k in ("effective_from", "effective_to"):
        if meta[k]:
            try:
                date.fromisoformat(meta[k])
            except ValueError:
                problems.append({"field": k, "problem": "must be a date like 2026-10-11"})
    if not re.fullmatch(r"[a-z0-9][a-z0-9-]{0,59}", meta["doc_key"]):
        problems.append({"field": "doc_key", "problem": "lowercase letters, digits and hyphens only"})
    if problems:
        raise ApiError(422, "validation_error", "The document's metadata is not valid.", details=problems)
    return meta


def create_document(conn, tenant: str, user_id: str, name: str, content_type: str, data: bytes, form: dict,
                    settings) -> tuple[dict, bool]:
    """Returns (the document row, duplicate). Raises ApiError for a file that is refused at once."""
    if not data:
        raise ApiError(422, "empty_file", "The file is empty.")
    if len(data) > settings.max_upload_bytes:
        raise ApiError(413, "file_too_large",
                       f"The file is {len(data):,} bytes; the limit is {settings.max_upload_bytes:,} bytes.")
    if not name.lower().endswith(SUFFIXES):
        raise ApiError(415, "unsupported_file", "Upload a .md, .txt, .html or .pdf file.")
    digest = hashlib.sha256(data).hexdigest()
    same = conn.execute(f"SELECT {DOC_COLUMNS} FROM documents WHERE tenant_id = %s AND sha256 = %s",
                        (tenant, digest)).fetchone()
    if same:
        return same, True
    meta = metadata(name, data, form, settings.today_date())
    try:
        with conn.transaction():
            row = conn.execute(
                "INSERT INTO documents (tenant_id, doc_key, version, title, doc_type, language, access, effective_from,"
                " effective_to, file_name, content_type, size_bytes, sha256, uploaded_by)"
                " VALUES (%s, %s, %s, %s, %s, %s, %s, %s, nullif(%s, '')::date, %s, %s, %s, %s, %s)"
                f" RETURNING {DOC_COLUMNS}",
                (tenant, meta["doc_key"], meta["version"], meta["title"], meta["doc_type"], meta["language"],
                 meta["access"], meta["effective_from"], meta["effective_to"], name, content_type or "",
                 len(data), digest, user_id)).fetchone()
            conn.execute("INSERT INTO document_files (tenant_id, document_id, data) VALUES (%s, %s, %s)",
                         (tenant, row["document_id"], data))
    except psycopg.errors.UniqueViolation as e:
        if "documents_same_file_once" in str(e):   # the same file, uploaded at the same moment
            same = conn.execute(f"SELECT {DOC_COLUMNS} FROM documents WHERE tenant_id = %s AND sha256 = %s",
                                (tenant, digest)).fetchone()
            return same, True
        raise ApiError(409, "conflict", f"Version {meta['version']} of {meta['doc_key']} already exists. "
                       "Upload it with a new version number, or delete the old one first.") from None
    except psycopg.errors.CheckViolation:
        raise ApiError(422, "validation_error", "effective_to must not be before effective_from.") from None
    return row, False
