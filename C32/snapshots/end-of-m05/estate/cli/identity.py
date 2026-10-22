"""Identities and credentials: commands of python -m estate."""

import json
import sys

from estate import paths
from estate.cli import actor as _actor


def cmd_credentials(a):
    from estate import configstore, identity

    if a.action == "issue":
        try:
            cid, _ = identity.issue_credentials(a.id, _actor(a))
        except (KeyError, ValueError) as e:
            sys.exit(str(e))
        where = paths.state() / "credentials" / f"{cid}.json"
        shown = where.relative_to(paths.PROJECT) if paths.PROJECT in where.parents else where
        print(f"New credentials for {cid}: client ID {cid}; the secret is in {shown} "
              "(shown nowhere else; keep it out of code and out of Git).")
    else:
        n = identity.revoke(a.id, _actor(a), a.reason)
        print(f"Revoked {n} credential(s) of {a.id}. Tokens issued before now are refused too.")
        ok, asked = configstore.push()
        if asked:
            print(f"Told {ok} of {asked} gateway replicas to refresh now.")


def cmd_token(a):
    from estate import identity

    creds = json.loads((paths.state() / "credentials" / f"{a.id}.json").read_text())
    try:
        t = identity.token(creds["client_id"], creds["client_secret"], a.audience)
    except identity.TokenError as e:
        sys.exit(f"{e.code}: {e}")
    if a.claims:
        import jwt

        print(json.dumps({"header": jwt.get_unverified_header(t["access_token"]),
                          "claims": jwt.decode(t["access_token"], options={"verify_signature": False})}, indent=1))
    else:
        print(t["access_token"])


ORDER = 21


def register(sub) -> dict:
    p = sub.add_parser("credentials", help="issue or revoke an agent's credentials")
    p.add_argument("action", choices=["issue", "revoke"])
    p.add_argument("id")
    p.add_argument("--reason", default="")
    p.add_argument("--by")
    p = sub.add_parser("token", help="get an access token with an agent's credentials (to look at it)")
    p.add_argument("id")
    p.add_argument("--audience", default="model-gateway")
    p.add_argument("--claims", action="store_true")
    return {"credentials": cmd_credentials, "token": cmd_token}
