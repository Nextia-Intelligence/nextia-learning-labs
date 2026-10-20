"""Browser checks of the help desk web app (optional).

Start the app first, in another terminal:  python -m helpdesk serve
Then run, in the practice-app folder:      python -m pytest ../workspace/ui/test_chat_ui.py
Test data only: test customer C-1001 (Alex Martin, test).
"""

import os
import re

from playwright.sync_api import expect, sync_playwright

URL = os.environ.get("HELPDESK_URL", "http://localhost:8730")


def open_new_conversation(page, seed):
    page.goto(URL)
    page.get_by_label("Test customer").select_option("C-1001")
    page.get_by_label("Seed").fill(seed)
    page.get_by_role("button", name="New conversation").click()


def send(page, text):
    page.get_by_role("textbox", name="Message").fill(text)
    page.get_by_role("button", name="Send").click()


def test_reply_shows_answer_source_and_trace():
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page()
        open_new_conversation(page, "1")
        send(page, "Do gift cards expire?")

        reply = page.locator(".msg.bot")
        expect(reply).to_have_count(1)
        expect(reply).to_contain_text("never expire")
        expect(reply.get_by_role("link")).to_have_attribute("href", re.compile(r"^/policies/gift-cards/"))

        trace_button = reply.get_by_role("button", name=re.compile(r"^tr-\d+-1$"))
        trace_id = trace_button.inner_text()
        trace_button.click()
        expect(page.locator("#trace")).to_contain_text(f'"trace_id": "{trace_id}"')
        browser.close()


def test_empty_message_gets_a_reply_not_an_error():
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page()
        open_new_conversation(page, "1")
        send(page, " ")

        reply = page.locator(".msg.bot")
        expect(reply).to_have_count(1)
        expect(reply).not_to_contain_text("Error")
        browser.close()
