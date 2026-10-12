"""Who is calling. Module 3: nobody signs in yet; every request acts as one practice user
(DEV_USER, Sam by default). Module 4 replaces this with a real sign-in and access tokens."""

from dataclasses import dataclass

from fastapi import APIRouter, Request

router = APIRouter()


@dataclass(frozen=True)
class Identity:
    user_id: str
    via: str              # dev (Module 4 adds token and session)


def identify(request: Request) -> Identity:
    return Identity(request.app.state.settings.dev_user, "dev")


@router.get("/auth/session")
def session(request: Request):
    return {"user_id": request.app.state.settings.dev_user, "name": "", "csrf_token": "", "via": "dev"}
