"""LESSON 6 -- Page Object Model in practice.

Compare this file with tests/01_basics/test_01_first_test.py. Same coverage,
but:
  * no CSS/labels leak into the test -- if the login form is redesigned you
    change ONE file (pages/login_page.py), not fifty tests
  * the test reads as intent: "log in with bad credentials, expect an error"
  * data comes from test-data/users.json, so adding a case is a JSON edit

POM is not free. It is worth it above roughly 20 tests, or as soon as two tests
share a flow.
"""

import pytest
from playwright.sync_api import expect

from utils.data_factory import login_cases


@pytest.mark.smoke
def test_valid_login(login_page) -> None:
    dashboard = login_page.login("demo", "Password123")

    expect(dashboard.welcome).to_have_text("Welcome back, demo.")
    expect(dashboard.nav.current_user).to_contain_text("demo")
    assert dashboard.current_url.endswith("/dashboard")


@pytest.mark.parametrize(
    "case",
    login_cases("valid_logins"),
    ids=lambda c: c["label"].replace(" ", "-"),
)
def test_all_valid_users_can_log_in(login_page, case) -> None:
    """Data-driven: one test function, N test cases, N separate results.

    `ids=` matters more than it looks -- it is what makes the CI failure say
    `test_all_valid_users_can_log_in[admin-user]` instead of `[case1]`.
    """
    dashboard = login_page.login(case["username"], case["password"])
    expect(dashboard.welcome).to_contain_text(case["username"])


@pytest.mark.parametrize(
    "case",
    login_cases("invalid_logins"),
    ids=lambda c: c["case"].replace(" ", "-"),
)
def test_invalid_logins_are_rejected(login_page, case) -> None:
    result = login_page.login_expecting_failure(case["username"], case["password"])

    expect(result.error_banner).to_be_visible()
    expect(result.error_banner).to_have_text("Invalid username or password")
    # The error must not leak WHICH half was wrong -- a real security assertion.
    assert "user" not in result.error_text().lower().replace("username", "")


@pytest.mark.smoke
def test_logout_returns_to_login(login_page) -> None:
    dashboard = login_page.login("demo", "Password123")
    dashboard.nav.logout()

    expect(dashboard.page.get_by_role("heading", name="Sign in")).to_be_visible()


def test_dashboard_requires_authentication(page, base_url) -> None:
    """Direct navigation without a session must redirect. Cheap, high-value
    security regression test -- run it in smoke on a real product."""
    page.goto("/dashboard")
    expect(page).to_have_url(f"{base_url}/")
    expect(page.get_by_role("heading", name="Sign in")).to_be_visible()
