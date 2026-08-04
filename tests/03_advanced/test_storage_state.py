"""LESSON 9 -- Reuse authentication instead of logging in 200 times.

The maths: 200 tests x 3.5s of login = ~12 minutes of CI per browser, per
shard, per run. Storage state reduces that to one login per session.

How it works: after logging in once, `context.storage_state()` serialises
cookies + localStorage to JSON. Any new context created with
`storage_state=...` starts already authenticated.

Security note: that JSON contains live session tokens. It is in .gitignore and
must NEVER be committed or uploaded as a CI artifact.
"""

import json
from pathlib import Path

import pytest
from playwright.sync_api import Browser, expect

from pages.dashboard_page import DashboardPage


@pytest.mark.smoke
def test_authenticated_page_skips_the_login_form(authenticated_page) -> None:
    authenticated_page.goto("/dashboard")

    # We never touched the login form in this test.
    expect(authenticated_page.get_by_test_id("welcome")).to_have_text("Welcome back, demo.")
    expect(authenticated_page.get_by_role("heading", name="Sign in")).to_have_count(0)


def test_storage_state_file_shape(storage_state_path: str) -> None:
    state = json.loads(Path(storage_state_path).read_text(encoding="utf-8"))

    assert "cookies" in state
    assert "origins" in state
    assert any(cookie["name"] == "session" for cookie in state["cookies"])


def test_two_contexts_are_isolated(
    browser: Browser, base_url: str, storage_state_path: str
) -> None:
    """Authenticated and anonymous side by side, in the same browser process.

    Contexts are cheap (milliseconds) and fully isolated -- this is the
    mechanism that makes Playwright parallelism safe.
    """
    authed = browser.new_context(base_url=base_url, storage_state=storage_state_path)
    anon = browser.new_context(base_url=base_url)

    authed_page, anon_page = authed.new_page(), anon.new_page()
    authed_page.goto("/dashboard")
    anon_page.goto("/dashboard")

    expect(authed_page.get_by_test_id("welcome")).to_be_visible()
    expect(anon_page.get_by_role("heading", name="Sign in")).to_be_visible()

    authed.close()
    anon.close()


def test_page_object_works_with_saved_session(authenticated_page) -> None:
    dashboard = DashboardPage(authenticated_page).open().load_users()
    expect(dashboard.rows).to_have_count(5)
