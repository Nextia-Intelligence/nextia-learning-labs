"""Who may do what, in which shop (Module 4). The token says WHO the caller is; this file reads
WHAT they may do from the database's memberships, for the shop named in the request's path.

Roles and what they allow:
    owner      ask, upload, delete; reads public and staff-only documents
    staff      ask, upload, delete; reads public and staff-only documents
    read_only  ask only; reads public documents only (a staff-only procedure is never retrieved)

A caller with no membership in the shop gets 404, the same answer as for a shop that does not
exist: an outsider cannot even learn which shops use the assistant. A member whose role is too
small gets 403. (The authentication course's order: identity 401 -> membership 404 -> role 403.)
"""

from dataclasses import dataclass

from .errors import ApiError, not_found

ROLE_ACCESS = {"owner": ("public", "staff"), "staff": ("public", "staff"), "read_only": ("public",)}
CAN_CHANGE = ("owner", "staff")


@dataclass(frozen=True)
class Principal:
    user_id: str
    name: str
    tenant_id: str
    shop: str            # the shop's name, for the prompt
    role: str

    @property
    def access_levels(self) -> tuple[str, ...]:
        return ROLE_ACCESS[self.role]


def membership(conn, user_id: str, tenant_id: str) -> Principal:
    row = conn.execute(
        "SELECT u.user_id, u.name, t.tenant_id, t.name AS shop, m.role FROM memberships m"
        " JOIN users u ON u.user_id = m.user_id JOIN tenants t ON t.tenant_id = m.tenant_id"
        " WHERE m.user_id = %s AND m.tenant_id = %s", (user_id, tenant_id)).fetchone()
    if row is None:
        raise not_found()
    return Principal(row["user_id"], row["name"], row["tenant_id"], row["shop"], row["role"])


def require_change(p: Principal) -> None:
    if p.role not in CAN_CHANGE:
        raise ApiError(403, "forbidden", f"Your role in {p.shop} ({p.role}) cannot upload or delete documents.")
