"""Fixtures shared by all tests (but not by the app or tooling).

Key idea: a fixture is just dependency injection with a lifecycle. Scope it as
widely as is SAFE -- session-scoped state that tests mutate is how suites turn
flaky under -n auto.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest
from playwright.sync_api import APIRequestContext, Browser, Page, Playwright

from utils.config import settings

AUTH_DIR = Path(".auth")


@pytest.fixture(scope="session")
def api_context(playwright: Playwright, base_url: str) -> APIRequestContext:
    """A browserless HTTP client that shares Playwright's networking stack.

    Use it for API tests and, more importantly, for FAST SETUP of UI tests:
    creating a user over HTTP takes 20ms; creating one by driving a form takes
    4 seconds. Only test the UI through the UI when the UI is what you're
    testing.
    """
    context = playwright.request.new_context(
        base_url=base_url,
        extra_http_headers={"Accept": "application/json"},
    )
    yield context
    context.dispose()


@pytest.fixture(autouse=True)
def reset_backend(api_context: APIRequestContext, request):
    """Restore seed data before every test that touches the API or dashboard.

    Independence is the property that makes a suite parallelisable and its
    failures meaningful. A test that only passes when run after another test is
    not a test, it is a trap.
    """
    # Skip for tests that do not touch our backend at all. The `external`
    # tests target public sites and their CI job never starts the local app --
    # without this guard every one of them errors on ConnectionRefused before
    # it runs. An autouse fixture reaches tests you were not thinking about;
    # always give it an escape hatch.
    if "no_reset" in request.keywords or "external" in request.keywords:
        yield
        return

    api_context.post("/api/reset")
    yield


@pytest.fixture(scope="session")
def storage_state_path(browser: Browser, base_url: str, worker_id: str) -> str:
    """Log in ONCE per session and save cookies/localStorage to disk.

    Every subsequent test starts already authenticated, skipping the login form.
    On a 200-test suite this routinely saves 10+ minutes of CI time.

    Trade-off to understand: tests now share an identity. If a test mutates that
    user's data, it leaks. Use a per-worker account in real projects.
    """
    AUTH_DIR.mkdir(exist_ok=True)
    # Per-worker filename: four xdist workers writing one path is a corrupt-file
    # race that shows up as a baffling "invalid storage state" error.
    auth_state = AUTH_DIR / f"storage_state-{worker_id}.json"

    context = browser.new_context(base_url=base_url)
    page = context.new_page()
    page.goto("/")
    page.get_by_label("Username").fill(settings.username)
    page.get_by_label("Password").fill(settings.password)
    page.get_by_role("button", name="Log in").click()
    page.wait_for_url("**/dashboard")
    context.storage_state(path=str(auth_state))
    context.close()
    return str(auth_state)


@pytest.fixture
def authenticated_page(browser: Browser, base_url: str, storage_state_path: str) -> Page:
    """A fresh, isolated, already-logged-in page."""
    context = browser.new_context(base_url=base_url, storage_state=storage_state_path)
    page = context.new_page()
    page.set_default_timeout(settings.default_timeout_ms)
    yield page
    context.close()


@pytest.fixture
def tmp_text_file(tmp_path: Path) -> Path:
    """pytest's tmp_path gives each test its own directory -- parallel safe."""
    file_path = tmp_path / "sample-upload.txt"
    file_path.write_text("line one\nline two\nline three\n", encoding="utf-8")
    return file_path


@pytest.fixture
def users_json() -> dict:
    return json.loads(Path("test-data/users.json").read_text(encoding="utf-8"))
