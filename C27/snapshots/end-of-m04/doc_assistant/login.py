"""Sign-in for the browser page, and who is calling (Module 4).

The page signs in through the API (a backend for the frontend, as in the authentication course):

    GET  /auth/login      -> the identity provider's sign-in page (authorization code + PKCE)
    GET  /auth/callback   <- the provider sends the browser back with a code; the API exchanges it
                             for tokens, checks them, and sets the session cookie
    GET  /auth/session    the signed-in user and the CSRF token for the page
    POST /auth/logout     clears the cookie

The session cookie (assistant_session) is HttpOnly (JavaScript cannot read it), SameSite=Lax,
Secure unless SESSION_COOKIE_SECURE=false (only on your own computer, over http), and lasts at
most 8 hours. It holds the user ID, the expiry and a CSRF token, signed with SESSION_SECRET
(HMAC-SHA256): the browser cannot change it. It holds no token of the provider. A request that
changes something (POST, DELETE) with the cookie must also send X-CSRF-Token.

Scripts and other programs send an access token instead: Authorization: Bearer <token>.
Either way, the identity gives only WHO; the shop and the role come from the memberships.
"""

import base64
import hashlib
import hmac
import json
import secrets
import time
from dataclasses import dataclass
from urllib.parse import urlencode

import httpx
from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse, RedirectResponse

from .auth import ProviderUnavailable, TokenRejected, check_id_token
from .errors import ApiError

SESSION_COOKIE = "assistant_session"
LOGIN_COOKIE = "assistant_login"
SESSION_SECONDS = 8 * 3600
SAFE_METHODS = ("GET", "HEAD", "OPTIONS")

router = APIRouter()


@dataclass(frozen=True)
class Identity:
    user_id: str
    via: str              # token, session or dev


def _b64(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).decode().rstrip("=")


def sign(payload: dict, secret: str) -> str:
    body = _b64(json.dumps(payload, separators=(",", ":")).encode())
    mac = hmac.new(secret.encode(), body.encode(), hashlib.sha256).digest()
    return f"{body}.{_b64(mac)}"


def unsign(value: str, secret: str) -> dict | None:
    try:
        body, mac = value.split(".")
        good = _b64(hmac.new(secret.encode(), body.encode(), hashlib.sha256).digest())
        if not hmac.compare_digest(mac, good):
            return None
        payload = json.loads(base64.urlsafe_b64decode(body + "=" * (-len(body) % 4)))
    except (ValueError, json.JSONDecodeError):
        return None
    return payload if payload.get("exp", 0) > time.time() else None


def identify(request: Request) -> Identity:
    """Who is calling: a bearer token, a session cookie, or (AUTH_MODE=dev) the fixed dev user."""
    s = request.app.state.settings
    header = request.headers.get("authorization", "")
    if header.lower().startswith("bearer "):
        try:
            who = request.app.state.validator.validate(header[7:].strip())
        except TokenRejected as e:
            raise ApiError(401, "unauthenticated", f"The access token was refused: {e} ({e.code}).",
                           headers={"WWW-Authenticate": f'Bearer error="invalid_token", error_description="{e.code}"'}) \
                from None
        except ProviderUnavailable:
            raise ApiError(503, "identity_provider_unavailable", "The identity provider cannot be reached.") from None
        return Identity(who.user_id, "token")
    cookie = request.cookies.get(SESSION_COOKIE)
    if cookie and s.session_secret:
        session = unsign(cookie, s.session_secret)
        if session:
            if request.method not in SAFE_METHODS and not hmac.compare_digest(
                    request.headers.get("x-csrf-token", ""), session["csrf"]):
                raise ApiError(403, "csrf_failed", "This request needs the page's X-CSRF-Token header.")
            return Identity(session["sub"], "session")
    if s.auth_mode == "dev":
        return Identity(s.dev_user, "dev")
    raise ApiError(401, "unauthenticated", "Sign in first.", headers={"WWW-Authenticate": "Bearer"})


def _cookie(response, name: str, value: str, max_age: int, s) -> None:
    response.set_cookie(name, value, max_age=max_age, httponly=True, samesite="lax", secure=s.session_cookie_secure,
                        path="/")


@router.get("/auth/login")
def login(request: Request, return_to: str = "/app/"):
    s = request.app.state.settings
    if not s.session_secret or not s.oidc_client_secret:
        raise ApiError(503, "sign_in_not_set_up", "Sign-in is not set up: run python -m idp init, then restart.")
    if not return_to.startswith("/") or return_to.startswith("//"):
        return_to = "/app/"          # only a local path: never an open redirect
    state, nonce, verifier = secrets.token_urlsafe(24), secrets.token_urlsafe(24), secrets.token_urlsafe(48)
    challenge = _b64(hashlib.sha256(verifier.encode()).digest())
    try:
        authorize = request.app.state.validator.provider.discovery()["authorization_endpoint"]
    except ProviderUnavailable:
        raise ApiError(503, "identity_provider_unavailable", "The identity provider cannot be reached.") from None
    query = urlencode({"response_type": "code", "client_id": s.oidc_client_id,
                       "redirect_uri": f"{s.public_url}/auth/callback", "scope": "openid profile documents:read "
                       "documents:write", "state": state, "nonce": nonce, "code_challenge": challenge,
                       "code_challenge_method": "S256"})
    response = RedirectResponse(f"{authorize}?{query}", status_code=302)
    _cookie(response, LOGIN_COOKIE, sign({"state": state, "nonce": nonce, "verifier": verifier,
                                          "return_to": return_to, "exp": time.time() + 600}, s.session_secret), 600, s)
    return response


@router.get("/auth/callback")
def callback(request: Request, code: str = "", state: str = "", error: str = ""):
    s = request.app.state.settings
    pending = unsign(request.cookies.get(LOGIN_COOKIE, ""), s.session_secret) if s.session_secret else None
    if error or not pending or not hmac.compare_digest(state, pending["state"]):
        raise ApiError(400, "sign_in_failed", "The sign-in did not complete. Start again from the page.")
    validator = request.app.state.validator
    try:
        token_url = validator.provider.endpoint("token_endpoint")
        reply = httpx.post(token_url, data={"grant_type": "authorization_code", "code": code,
                                            "redirect_uri": f"{s.public_url}/auth/callback",
                                            "code_verifier": pending["verifier"]},
                           auth=(s.oidc_client_id, s.oidc_client_secret), timeout=5.0)
        tokens = reply.json() if reply.status_code == 200 else {}
        if not tokens:
            raise ApiError(400, "sign_in_failed", "The identity provider refused the sign-in code.")
        claims = check_id_token(validator.provider, tokens["id_token"], s.oidc_client_id, pending["nonce"])
        who = validator.validate(tokens["access_token"])
    except (TokenRejected, KeyError, httpx.HTTPError, ProviderUnavailable):
        raise ApiError(400, "sign_in_failed", "The sign-in tokens could not be checked.") from None
    if claims["sub"] != who.user_id:
        raise ApiError(400, "sign_in_failed", "The ID token and the access token name different people.")
    response = RedirectResponse(pending["return_to"], status_code=302)
    session = {"sub": who.user_id, "name": claims.get("name", ""), "csrf": secrets.token_urlsafe(24),
               "exp": time.time() + SESSION_SECONDS}
    _cookie(response, SESSION_COOKIE, sign(session, s.session_secret), SESSION_SECONDS, s)
    response.delete_cookie(LOGIN_COOKIE, path="/")
    return response


@router.get("/auth/session")
def session(request: Request):
    s = request.app.state.settings
    data = unsign(request.cookies.get(SESSION_COOKIE, ""), s.session_secret) if s.session_secret else None
    if data:
        return {"user_id": data["sub"], "name": data["name"], "csrf_token": data["csrf"], "via": "session"}
    if s.auth_mode == "dev":
        return {"user_id": s.dev_user, "name": "", "csrf_token": "", "via": "dev"}
    raise ApiError(401, "unauthenticated", "Not signed in.")


@router.post("/auth/logout")
def logout(request: Request):
    identify(request)   # the CSRF check: another site cannot sign you out
    response = JSONResponse({"signed_out": True})
    response.delete_cookie(SESSION_COOKIE, path="/")
    return response
