"""The caller of a request, in the shop named in the path.

Module 3: the practice user acts in whichever shop the path names, as long as the shop exists.
Nothing checks that the user belongs to that shop yet: Module 4 adds the membership check.
"""

from fastapi import Request

from .access import Principal
from .errors import not_found
from .login import identify


def principal(request: Request, tenant: str) -> Principal:
    who = identify(request)
    with request.app.state.db.admin() as conn:
        shop = conn.execute("SELECT name FROM tenants WHERE tenant_id = %s", (tenant,)).fetchone()
        user = conn.execute("SELECT name FROM users WHERE user_id = %s", (who.user_id,)).fetchone()
    if shop is None:
        raise not_found()
    request.state.user_id, request.state.tenant = who.user_id, tenant
    return Principal(who.user_id, user["name"] if user else who.user_id, tenant, shop["name"], "staff")
