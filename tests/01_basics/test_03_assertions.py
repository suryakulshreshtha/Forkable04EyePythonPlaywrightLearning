"""LESSON 3 -- Web-first assertions vs plain asserts.

    expect(locator).to_have_text("x")   # polls, retries, then fails w/ context
    assert locator.inner_text() == "x"  # single snapshot in time

The first one waits for the app to catch up. The second one races it. In a
suite of any size that difference IS the flakiness.

Every expect() takes a `timeout=` override, and `.not_to_*` inverts it.
"""

import re

import pytest
from playwright.sync_api import Page, expect


@pytest.fixture(autouse=True)
def _logged_in(page: Page) -> None:
    page.goto("/")
    page.get_by_label("Username").fill("demo")
    page.get_by_label("Password").fill("Password123")
    page.get_by_role("button", name="Log in").click()
    expect(page).to_have_url(re.compile(r"/dashboard$"))


def test_visibility_and_state_assertions(page: Page) -> None:
    table = page.get_by_role("table", name="Users")

    expect(table).to_be_hidden()  # not rendered yet
    expect(page.get_by_test_id("table-status")).to_have_text("No data loaded yet.")

    page.get_by_role("button", name="Load users").click()

    # The click triggers a 700ms fake latency + a fetch. We do NOT sleep.
    # to_be_visible() polls every ~100ms until it passes or times out.
    expect(table).to_be_visible()
    expect(page.get_by_test_id("user-row")).to_have_count(5)


def test_text_assertions(page: Page) -> None:
    page.get_by_role("button", name="Load users").click()
    status = page.get_by_test_id("table-status")

    expect(status).to_have_text("Showing 5 of 5 users")  # exact
    expect(status).to_contain_text("5 users")  # substring
    expect(page.get_by_test_id("user-row").locator("td").first).to_have_text("1")


def test_list_assertions(page: Page) -> None:
    page.get_by_role("button", name="Load users").click()
    names = page.get_by_test_id("user-row").locator("td:nth-child(2)")

    # Asserts count AND order in one call -- catches sorting regressions.
    expect(names).to_have_text(
        ["Ada Lovelace", "Alan Turing", "Grace Hopper", "Edsger Dijkstra", "Barbara Liskov"]
    )


def test_attribute_and_value_assertions(page: Page) -> None:
    page.get_by_role("link", name="Upload").click()
    file_input = page.get_by_label("Document")

    expect(file_input).to_have_attribute("accept", ".txt,.csv")
    expect(page).to_have_url(re.compile(r"/upload$"))


def test_negative_assertions_and_custom_timeout(page: Page) -> None:
    # not_to_* is not the same as "assert it is absent right now" -- it waits
    # for the condition to become true, which is usually what you want.
    expect(page.get_by_role("alert")).not_to_be_visible()

    # A tighter timeout on an assertion you EXPECT to pass instantly keeps
    # failures fast.
    expect(page.get_by_test_id("welcome")).to_be_visible(timeout=2000)


def test_soft_assertions_collect_multiple_failures(page: Page) -> None:
    """Soft assertions do not abort the test on first failure.

    Useful for "check 8 fields on this form" so one run tells you about all 8
    problems instead of only the first. Overuse hides real failures -- keep the
    hard assert for the thing the test is actually about.
    """
    page.get_by_role("button", name="Load users").click()
    expect.soft(page.get_by_test_id("table-status")).to_contain_text("Showing")
    expect.soft(page.get_by_role("table", name="Users")).to_be_visible()
    expect(page.get_by_test_id("user-row")).to_have_count(5)


# YOUR TURN (exercise 3):
# Load users, filter by role "admin", and assert with ONE expect() call that
# exactly the two admin names appear, in order.
