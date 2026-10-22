"""One identity per agent: client credentials, and short-lived signed access tokens.

Every registered agent gets its own client ID (its registration ID) and a secret (shown once; the registry
keeps only a hash). With them it asks the estate's token endpoint (estate/server.py, POST /oauth/token,
the OAuth 2.0 client credentials grant) for an access token: a JWT signed with RS256, the same shape as the
authentication and MCP courses' tokens (typ at+jwt, iss, sub, aud, exp, nbf, iat, jti, client_id, scope). The
token carries no team, no role and no permissions: the gateways read those from the registry's configuration.

Signing and checking use PyJWT and cryptography: no cryptography is written by hand here.
"""

import hashlib
import hmac
import json
import secrets
import uuid
from contextlib import closing

import jwt
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import rsa

from estate import clock, paths, registry

ISSUER = "larkfield-estate"
AUDIENCES = ("model-gateway", "tool-gateway")
TOKEN_SECONDS = 600
LEEWAY_SECONDS = 30


class TokenError(Exception):
    """A token or a credential that the platform refuses. `code` is what the caller sees."""

    def __init__(self, code: str, message: str):
        super().__init__(message)
        self.code = code


def _key_path():
    return paths.state() / "identity" / "signing-key.pem"


def signing_key() -> rsa.RSAPrivateKey:
    path = _key_path()
    if not path.exists():
        path.parent.mkdir(parents=True, exist_ok=True)
        key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
        path.write_bytes(key.private_bytes(serialization.Encoding.PEM, serialization.PrivateFormat.PKCS8,
                                           serialization.NoEncryption()))
        path.chmod(0o600)
    return serialization.load_pem_private_key(path.read_bytes(), password=None)


def jwks() -> dict:
    """The public key, published so that every gateway replica can check tokens without asking anyone."""
    pub = signing_key().public_key()
    jwk = json.loads(jwt.algorithms.RSAAlgorithm.to_jwk(pub))
    jwk.update({"kid": kid(), "use": "sig", "alg": "RS256"})
    return {"keys": [jwk]}


def kid() -> str:
    pem = signing_key().public_key().public_bytes(serialization.Encoding.PEM,
                                                  serialization.PublicFormat.SubjectPublicKeyInfo)
    return hashlib.sha256(pem).hexdigest()[:16]


def _hash(secret: str) -> str:
    return hashlib.sha256(secret.encode()).hexdigest()


def issue_credentials(agent_id: str, actor: str) -> tuple[str, str]:
    """A new client secret for an agent (its old ones keep working until revoked). Returns (client_id, secret)."""
    reg = registry.get(agent_id)
    if reg is None:
        raise KeyError(f"No registration {agent_id}: register it first.")
    if reg.status == "retired":
        raise ValueError(f"{agent_id} is retired: it gets no credentials.")
    secret = "est-" + secrets.token_urlsafe(24)
    with closing(registry.db()) as con, con:
        con.execute("insert or replace into credentials values (?, ?, ?, ?, null)",
                    (agent_id, agent_id, _hash(secret), clock.iso()))
        registry.event(con, agent_id, "credentials_issued", actor)
        registry.bump(con)
    path = paths.state() / "credentials" / f"{agent_id}.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps({"client_id": agent_id, "client_secret": secret}) + "\n")
    path.chmod(0o600)
    return agent_id, secret


def revoke(agent_id: str, actor: str, reason: str) -> int:
    """Revoke every credential of the agent. Tokens issued before now are refused by the gateways too."""
    with closing(registry.db()) as con, con:
        n = con.execute("update credentials set revoked_at = ? where agent_id = ? and revoked_at is null",
                        (clock.iso(), agent_id)).rowcount
        registry.event(con, agent_id, "credentials_revoked", actor, reason=reason)
        registry.bump(con)
    return n


def revoked_before(agent_id: str) -> float | None:
    """The time (epoch seconds) of the agent's last revocation: tokens issued before it are dead."""
    with closing(registry.db()) as con:
        row = con.execute("select max(revoked_at) from credentials where agent_id = ?", (agent_id,)).fetchone()
    if not row or not row[0]:
        return None
    from datetime import datetime
    return datetime.fromisoformat(row[0]).timestamp()


def token(client_id: str, client_secret: str, audience: str) -> dict:
    """The client credentials grant: check the secret and the registration, then sign a short-lived token."""
    if audience not in AUDIENCES:
        raise TokenError("invalid_target", f"Unknown audience {audience!r}: model-gateway or tool-gateway.")
    with closing(registry.db()) as con:
        row = con.execute("select * from credentials where client_id = ?", (client_id,)).fetchone()
    if row is None or row["revoked_at"] or not hmac.compare_digest(row["secret_hash"], _hash(client_secret or "")):
        raise TokenError("invalid_client", "Unknown client, wrong secret, or revoked credentials.")
    reg = registry.get(row["agent_id"])
    if reg is None or reg.status not in ("active", "draining"):
        status = "not registered" if reg is None else reg.status
        raise TokenError("invalid_client", f"{client_id} cannot get a token: its registration is {status}.")
    t = int(clock.now().timestamp())
    claims = {"iss": ISSUER, "sub": reg.agent_id, "aud": audience, "iat": t, "nbf": t, "exp": t + TOKEN_SECONDS,
              "jti": uuid.uuid4().hex, "client_id": client_id,
              "scope": "model:call" if audience == "model-gateway" else "tools:call"}
    signed = jwt.encode(claims, signing_key(), algorithm="RS256", headers={"kid": kid(), "typ": "at+jwt"})
    return {"access_token": signed, "token_type": "Bearer", "expires_in": TOKEN_SECONDS, "scope": claims["scope"]}


class Verifier:
    """Checks tokens with the published key (JWKS), as a gateway replica does: no call to the issuer per request."""

    def __init__(self, jwks_doc: dict):
        self.keys = {k["kid"]: jwt.algorithms.RSAAlgorithm.from_jwk(json.dumps(k)) for k in jwks_doc["keys"]}

    def verify(self, token_text: str, audience: str, now: float | None = None) -> dict:
        if not token_text:
            raise TokenError("missing_token", "Send your access token: Authorization: Bearer <token>.")
        try:
            header = jwt.get_unverified_header(token_text)
        except jwt.PyJWTError:
            raise TokenError("invalid_token", "The token is not a JWT.") from None
        if header.get("typ") != "at+jwt":
            raise TokenError("invalid_token", "This is not an access token (typ at+jwt).")
        if header.get("alg") != "RS256":
            raise TokenError("invalid_token", "Algorithm not allowed.")
        key = self.keys.get(header.get("kid"))
        if key is None:
            raise TokenError("invalid_token", "Unknown signing key.")
        try:
            # The times are checked below against the estate's clock (a replayed month moves it).
            claims = jwt.decode(token_text, key, algorithms=["RS256"], audience=audience, issuer=ISSUER,
                                options={"require": ["exp", "iat", "nbf", "sub", "jti"], "verify_exp": False,
                                         "verify_nbf": False, "verify_iat": False})
        except jwt.InvalidAudienceError:
            raise TokenError("wrong_audience", f"This token is not for the {audience}.") from None
        except jwt.PyJWTError as e:
            raise TokenError("invalid_token", f"The token is not valid ({type(e).__name__}).") from None
        t = now if now is not None else now_epoch()
        if claims["exp"] + LEEWAY_SECONDS < t:
            raise TokenError("expired_token", "The token has expired: get a new one.")
        if claims["nbf"] - LEEWAY_SECONDS > t:
            raise TokenError("invalid_token", "The token is not valid yet.")
        return claims


def now_epoch() -> float:
    return clock.now().timestamp()
