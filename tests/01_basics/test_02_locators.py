"""LESSON 2 -- Locators: how to find things without writing brittle selectors.

The priority order that professional teams use:

    get_by_role        <- how a user/screen-reader sees it. Most robust.
    get_by_label       <- form controls. Forces accessible markup.
    get_by_placeholder <- only when there is no label (there should be a label)
    get_by_text        <- non-interactive content
    get_by_test_id     <- an explicit contract with the dev team
    CSS                <- structural, acceptable
    XPath              <- avoid; unreadable and breaks on any DOM reshuffle

A locator is LAZY and AUTO-RETRYING. `page.get_by_role(...)` does not query the
DOM; it describes how to query it, and re-queries on every action. That is why
Playwright does not suffer from stale-element exceptions.
"""

import re

import pytest
from playwright.sync_api import Page, expect


@pytest.fixture(autouse=True)
def _open_login(page: Page) -> None:
    page.goto("/")


def test_all_the_ways_to_find_the_username_field(page: Page) -> None:
    by_label = page.get_by_label("Username")
    by_placeholder = page.get_by_placeholder("demo")
    by_css = page.locator("#username")
    by_xpath = page.locator("//input[@name='username']")  # shown for contrast only

    for locator in (by_label, by_placeholder, by_css, by_xpath):
        expect(locator).to_be_visible()

    # They all resolve to the same single element.
    assert by_label.count() == by_css.count() == 1


def test_get_by_role_with_name(page: Page) -> None:
    # `name` matches the ACCESSIBLE name, which is not always the inner text --
    # it also accounts for aria-label, alt text, and associated <label>s.
    expect(page.get_by_role("button", name="Log in")).to_be_visible()
    expect(page.get_by_role("heading", name="Sign in", level=1)).to_be_visible()

    # exact=False by default and case-insensitive; tighten it when needed.
    expect(page.get_by_role("button", name="log in", exact=False)).to_be_visible()


def test_text_matching_modes(page: Page) -> None:
    # Substring by default...
    expect(page.get_by_text("Try")).to_be_visible()
    # ...exact when you ask for it...
    expect(page.get_by_role("heading", name="Sign in", exact=True)).to_be_visible()
    # ...or a regex for anything fuzzier.
    expect(page.get_by_text(re.compile(r"password123", re.IGNORECASE))).to_be_visible()


def test_chaining_and_filtering(page: Page) -> None:
    page.goto("/")
    page.get_by_label("Username").fill("demo")
    page.get_by_label("Password").fill("Password123")
    page.get_by_role("button", name="Log in").click()
    page.get_by_role("button", name="Load users").click()

    rows = page.get_by_test_id("user-row")

    # Chaining scopes the search to a parent -- prefer this over long CSS.
    expect(rows.filter(has_text="Ada Lovelace")).to_have_count(1)

    # has= filters by a DESCENDANT locator, not by text.
    admins = rows.filter(has=page.get_by_text("admin", exact=True))
    expect(admins).to_have_count(2)

    # nth / first / last exist, but positional locators are the brittlest kind.
    # Reach for filter() before you reach for nth().
    expect(rows.first).to_be_visible()


def test_strict_mode_protects_you(page: Page) -> None:
    """Playwright is strict by default: a locator that matches 2+ elements
    raises instead of silently picking the first one.

    This is a FEATURE. Selenium's findElement silently returning element[0] has
    caused more false-green tests than almost anything else.
    """
    # Aside worth knowing: get_by_role("textbox") would match only ONE element
    # here, because <input type="password"> has no implicit ARIA role. Roles are
    # not a synonym for tag names -- check the ARIA spec when a role locator
    # surprises you.
    ambiguous = page.locator("form input")  # username, password, remember-me
    assert ambiguous.count() == 3

    with pytest.raises(Exception, match="strict mode violation"):
        ambiguous.fill("boom", timeout=2000)


# YOUR TURN (exercise 2):
# The dashboard has a "Role" <select>. Find it three different ways and assert
# it has exactly 4 options. Solution: docs/solutions/exercise-02.md
