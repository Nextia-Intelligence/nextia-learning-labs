"""The caller of a request, in the shop named in the path: identity first, then membership."""

from fastapi import Request

from .access import Principal, membership
from .login import identify


def principal(request: Request, tenant: str) -> Principal:
    who = identify(request)                       # 401 when nobody is signed in
    with request.app.state.db.admin() as conn:    # memberships: read on every request, never cached
        p = membership(conn, who.user_id, tenant)  # 404 when the caller is not a member of this shop
    request.state.user_id, request.state.tenant = p.user_id, p.tenant_id
    return p
