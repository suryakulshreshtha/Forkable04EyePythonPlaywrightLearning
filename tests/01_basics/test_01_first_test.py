"""LESSON 1 -- Your very first Playwright test.

Run just this file:
    pytest tests/01_basics/test_01_first_test.py -v
Watch it happen:
    pytest tests/01_basics/test_01_first_test.py --headed --slowmo 800

Three things to notice
----------------------
1. `page` is a fixture from pytest-playwright. You never create or close a
   browser yourself; each test gets a brand-new browser CONTEXT (think: fresh
   incognito profile), so tests cannot leak cookies into each other.
2. `expect(...)` is a WEB-FIRST assertion. It polls until the condition is true
   or the timeout expires. `assert locator.inner_text() == "x"` does not poll
   and is the number one cause of flaky beginner tests.
3. Relative URLs work because we set base_url in conftest.py.
"""

import re

import pytest
from playwright.sync_api import Page, expect


@pytest.mark.smoke
def test_login_page_loads(page: Page) -> None:
    page.goto("/")

    # Assert on the page, not on an element -- both styles exist.
    expect(page).to_have_title("Sign in | Forkable04Eye")
    expect(page.get_by_role("heading", name="Sign in")).to_be_visible()
    expect(page.get_by_role("button", name="Log in")).to_be_enabled()


@pytest.mark.smoke
def test_successful_login_reaches_dashboard(page: Page) -> None:
    page.goto("/")
    page.get_by_label("Username").fill("demo")
    page.get_by_label("Password").fill("Password123")
    page.get_by_role("button", name="Log in").click()

    # to_have_url waits for the navigation -- no wait_for_navigation needed.
    # NOTE: a plain STRING is compared exactly (after base_url resolution).
    # For "ends with /dashboard" you want a regex. Getting this wrong is a
    # classic first-week confusion.
    expect(page).to_have_url(re.compile(r"/dashboard$"))
    expect(page.get_by_test_id("welcome")).to_have_text("Welcome back, demo.")


def test_failed_login_shows_error(page: Page) -> None:
    page.goto("/")
    page.get_by_label("Username").fill("demo")
    page.get_by_label("Password").fill("definitely-wrong")
    page.get_by_role("button", name="Log in").click()

    error = page.get_by_role("alert")
    expect(error).to_be_visible()
    expect(error).to_contain_text("Invalid username or password")
    # Still on the login page -- assert the negative too.
    expect(page).not_to_have_url(re.compile(r"/dashboard$"))


# YOUR TURN (exercise 1):
# Write a test that logs in as `admin` / `Admin123` and asserts the nav bar
# shows "Signed in as admin". Solution: docs/solutions/exercise-01.md
