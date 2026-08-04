"""LESSON 14 -- Testing sites you do not control.

Everything here is auto-marked `external` (see the collection hook in the root
conftest.py) and runs with `continue-on-error: true` in CI.

Why they are quarantined
------------------------
You do not own these sites. They can be down, rate-limited, geo-blocked, or
redesigned overnight. A test you cannot fix must never be able to block your
team's merge queue. This is the same reasoning you should apply at work to
third-party sandboxes and shared staging environments.

Run them deliberately:
    pytest -m external
Skip them (the default in `make test`):
    pytest -m "not external"
"""

import re

import pytest
from playwright.sync_api import Error as PlaywrightError
from playwright.sync_api import Page, expect

pytestmark = pytest.mark.external


def test_playwright_docs_homepage(page: Page) -> None:
    page.goto("https://playwright.dev/", wait_until="domcontentloaded")

    # Loose assertion on purpose: we do not control this page's copy.
    expect(page).to_have_title(re.compile("Playwright"))
    expect(page.get_by_role("link", name="Get started")).to_be_visible()


def test_playwright_docs_navigation(page: Page) -> None:
    page.goto("https://playwright.dev/python/", wait_until="domcontentloaded")

    expect(page.get_by_role("heading", name="Installation")).to_be_visible(timeout=15000)
    expect(page).to_have_url(re.compile(r"/python/"))


def test_the_internet_login_form(page: Page) -> None:
    """the-internet.herokuapp.com is the classic automation practice site."""
    page.goto("https://the-internet.herokuapp.com/login", wait_until="domcontentloaded")

    page.get_by_label("Username").fill("tomsmith")
    page.get_by_label("Password").fill("SuperSecretPassword!")
    page.get_by_role("button", name="Login").click()

    expect(page.locator("#flash")).to_contain_text("You logged into a secure area!")


def test_the_internet_dynamic_loading(page: Page) -> None:
    """Auto-waiting against a real site with a real spinner."""
    page.goto("https://the-internet.herokuapp.com/dynamic_loading/2", wait_until="domcontentloaded")

    page.get_by_role("button", name="Start").click()
    expect(page.get_by_text("Hello World!")).to_be_visible(timeout=20000)


def test_api_over_the_public_internet(playwright) -> None:
    """APIRequestContext against a public echo API -- no browser.

    Note the try/except: a DNS failure or a 503 from someone else's server is
    an ENVIRONMENT problem, not a product defect, so we `skip` rather than
    `fail`. Distinguishing those two is one of the more valuable habits an SDET
    can build -- a suite that cries wolf about infrastructure gets ignored.
    """
    request_context = playwright.request.new_context(base_url="https://httpbin.org")
    try:
        try:
            response = request_context.get("/json", timeout=20000)
        except PlaywrightError as exc:
            pytest.skip(f"httpbin.org is unreachable from this runner: {exc}")

        if response.status >= 500:
            pytest.skip(f"httpbin.org returned {response.status} -- their problem, not ours")

        assert response.ok
        assert "slideshow" in response.json()
    finally:
        request_context.dispose()
