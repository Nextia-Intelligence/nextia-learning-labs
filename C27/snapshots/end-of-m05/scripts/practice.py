"""Practice tokens for the scripts: a throw-away identity provider in a temporary folder.

The scripts run the API in their own process (FastAPI's TestClient). They sign in as people of
the identity data with tokens from this provider, and the API trusts only this provider's keys
during the run. Nothing is written to .idp/ or .env.
"""

import logging
import tempfile

from doc_assistant.auth import ProviderConfig, TokenValidator

ISSUER = "http://localhost:8400"


def practice_tokens():
    """Tokens signed by a throw-away practice provider, and a validator that trusts only it."""
    # the scripts print their own summary, not every request, model load or PDF warning
    # (the test client logs every request through "httpx2")
    for name in ("doc_assistant.access", "httpx", "httpx2", "sentence_transformers"):
        logging.getLogger(name).setLevel(logging.WARNING)
    logging.getLogger("pypdf").setLevel(logging.ERROR)
    from idp.store import Store
    from idp.tokens import Signer

    store = Store(tempfile.mkdtemp(prefix="practice-idp-"))
    store.init()
    signer = Signer(store, ISSUER)

    def fetch(url: str) -> dict:
        return {"issuer": ISSUER, "jwks_uri": f"{ISSUER}/jwks.json"} if "well-known" in url else store.jwks()

    def token(user: str) -> dict:
        return {"Authorization": f"Bearer {signer.access_token(user, 'practice', 'documents:read documents:write')}"}

    return token, TokenValidator(ProviderConfig(ISSUER, fetch=fetch), "doc-assistant")
