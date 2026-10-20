"""A browser check of the help desk web app (optional). Start the app first: python -m helpdesk serve --seed 1"""

import os
import re

from playwright.sync_api import expect, sync_playwright

URL = os.environ.get("HELPDESK_URL", "http://localhost:8730")


def test_reply_shows_trace_and_source():
    with sync_playwright() as p:
        browser = p.chromium.launch(args=["--use-mock-keychain", "--password-store=basic"])
        page = browser.new_page()
        page.goto(URL)
        page.get_by_label("Test customer").select_option("C-1001")
        page.get_by_placeholder("Type a message").fill("Do gift cards expire?")
        page.get_by_role("button", name="Send").click()
        reply = page.locator(".msg.bot").last
        expect(reply).to_contain_text("never expire")
        expect(reply).to_contain_text("Sources:")
        trace_button = reply.get_by_role("button", name=re.compile(r"^tr-\d{4}-1$"))
        expect(trace_button).to_be_visible()
        trace_button.click()
        expect(page.locator("#trace")).to_contain_text('"app_version": "2.3.0"')
        browser.close()
