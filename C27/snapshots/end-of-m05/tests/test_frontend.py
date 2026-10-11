"""The plain page: served by the API, accessible, and safe with the server's text."""

from pathlib import Path

STATIC = Path(__file__).resolve().parent.parent / "doc_assistant" / "static"


def test_the_page_is_served_with_its_forms(client):
    r = client.get("/app/")
    assert r.status_code == 200 and "text/html" in r.headers["content-type"]
    for needle in ('<label for="question">', '<label for="file">', 'id="ask-status" role="status"',
                   'aria-live="polite"', "<noscript>", '<caption'):
        assert needle in r.text
    assert client.get("/", follow_redirects=False).headers["location"] == "/app/"


def test_no_framework_no_build_and_nothing_from_other_sites():
    html = (STATIC / "index.html").read_text()
    assert 'src="app.js"' in html and "http" not in html.split("<body>")[0].replace("http-equiv", "")


def test_server_text_is_never_put_on_the_page_as_html():
    js = (STATIC / "app.js").read_text()
    assert "innerHTML" not in js and "insertAdjacentHTML" not in js and "textContent" in js


def test_the_page_has_a_state_for_every_step():
    js = (STATIC / "app.js").read_text()
    for state in ("Uploading", "Searching the documents", "No answer in the documents", "already here",
                  "Sign in", "cannot be reached"):
        assert state in js
