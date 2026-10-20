import re
from playwright.sync_api import Playwright, sync_playwright, expect


def run(playwright: Playwright) -> None:
    browser = playwright.chromium.launch(headless=False)
    context = browser.new_context()
    page = context.new_page()
    page.goto("http://localhost:8730/")
    page.get_by_label("Test customer").select_option("C-1001")
    page.get_by_role("textbox", name="Message").click()
    page.get_by_role("textbox", name="Message").fill("Do gift cards expire?")
    page.get_by_role("button", name="Send").click()
    expect(page.get_by_role("log")).to_contain_text("Thanks for asking. Gift cards never expire and have no fees. [1] I hope this helps.")
    page.get_by_role("button", name="tr-0001-1").click()
    expect(page.locator("#trace")).to_contain_text("\"app_version\": \"2.3.0\"")

    # ---------------------
    context.close()
    browser.close()


with sync_playwright() as playwright:
    run(playwright)
