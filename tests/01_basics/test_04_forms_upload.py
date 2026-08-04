"""LESSON 4 -- Interacting: fill, check, select, upload, download.

Every action here does an ACTIONABILITY check first: the element must be
attached, visible, stable (not animating), able to receive events (nothing on
top of it) and enabled. If any check fails, Playwright retries until timeout.
That is why you almost never need an explicit wait before a click.
"""

import re

import pytest
from playwright.sync_api import Page, expect


def test_fill_vs_type(page: Page) -> None:
    page.goto("/")
    username = page.get_by_label("Username")

    # fill() clears then sets the value in one operation. Fast, and it fires the
    # input event so React/Vue see it. Use this by default.
    username.fill("demo")
    expect(username).to_have_value("demo")

    # press_sequentially() emulates real keystrokes -- only needed when the app
    # reacts per-keypress (autocomplete, input masks, character counters).
    username.clear()
    username.press_sequentially("dem", delay=50)
    expect(username).to_have_value("dem")


def test_checkbox_and_keyboard(page: Page) -> None:
    page.goto("/")
    remember = page.get_by_label("Remember me")

    expect(remember).not_to_be_checked()
    remember.check()  # idempotent: no-op if already checked
    expect(remember).to_be_checked()
    remember.uncheck()
    expect(remember).not_to_be_checked()

    page.get_by_label("Username").fill("demo")
    page.get_by_label("Password").fill("Password123")
    page.get_by_label("Password").press("Enter")  # submit without clicking
    expect(page).to_have_url(re.compile(r"/dashboard$"))


@pytest.fixture
def dashboard(page: Page) -> Page:
    page.goto("/")
    page.get_by_label("Username").fill("demo")
    page.get_by_label("Password").fill("Password123")
    page.get_by_role("button", name="Log in").click()
    return page


def test_select_dropdown(dashboard: Page) -> None:
    dashboard.get_by_role("button", name="Load users").click()
    expect(dashboard.get_by_test_id("user-row")).to_have_count(5)

    dashboard.get_by_label("Role").select_option("admin")
    expect(dashboard.get_by_test_id("user-row")).to_have_count(2)

    dashboard.get_by_label("Role").select_option(label="dev")
    expect(dashboard.get_by_test_id("user-row")).to_have_count(2)

    dashboard.get_by_label("Role").select_option("")
    expect(dashboard.get_by_test_id("user-row")).to_have_count(5)


def test_upload_from_disk(dashboard: Page, tmp_text_file) -> None:
    dashboard.get_by_role("link", name="Upload").click()
    dashboard.get_by_label("Document").set_input_files(str(tmp_text_file))
    dashboard.get_by_role("button", name="Upload").click()

    expect(dashboard.get_by_test_id("uploaded-name")).to_have_text("sample-upload.txt")
    expect(dashboard.get_by_test_id("upload-preview")).to_contain_text("line two")


def test_upload_from_memory(dashboard: Page) -> None:
    """No temp file at all -- nothing to create, nothing to clean up.
    This is the CI-friendly way to test uploads."""
    dashboard.goto("/upload")
    dashboard.get_by_label("Document").set_input_files(
        files=[{"name": "in-memory.csv", "mimeType": "text/csv", "buffer": b"a,b\n1,2\n"}]
    )
    dashboard.get_by_role("button", name="Upload").click()
    expect(dashboard.get_by_test_id("uploaded-name")).to_have_text("in-memory.csv")


def test_download(dashboard: Page) -> None:
    """expect_download() must WRAP the click, not follow it -- otherwise the
    download can complete before you start listening."""
    with dashboard.expect_download() as download_info:
        dashboard.get_by_test_id("download-csv").click()

    download = download_info.value
    assert download.suggested_filename == "users-export.csv"

    content = download.path().read_text(encoding="utf-8")
    assert content.splitlines()[0] == "id,name,role"
    assert "Ada Lovelace" in content


# YOUR TURN (exercise 4):
# Combine the search box AND the role dropdown: filter to role=admin and name
# containing "grace", then assert exactly one row remains.
