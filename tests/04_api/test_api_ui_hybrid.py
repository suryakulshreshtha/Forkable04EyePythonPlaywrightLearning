"""LESSON 13 -- Hybrid tests: set up over the API, verify in the UI.

This is the single highest-leverage pattern in UI automation.

Slow way:  drive the "create user" form 5 times, then check the table. ~20s.
Fast way:  5 POSTs (~50ms), then check the table. ~2s.

You still get real UI coverage of the thing under test; you just stop
re-testing the create form in every single test.
"""

import pytest
from playwright.sync_api import APIRequestContext, Page, expect

from utils.data_factory import new_user

# These live in 04_api/ for narrative reasons but they DO launch a browser, so
# they are not part of the fast browserless lane. CI selects that lane with
#     pytest -m "api and not ui"
pytestmark = pytest.mark.ui


@pytest.mark.smoke
def test_api_created_user_appears_in_the_ui(
    api_context: APIRequestContext, authenticated_page: Page
) -> None:
    payload = new_user(role="tester")
    created = api_context.post("/api/users", data=payload).json()

    authenticated_page.goto("/dashboard")
    authenticated_page.get_by_role("button", name="Load users").click()

    row = authenticated_page.get_by_test_id("user-row").filter(has_text=payload["name"])
    expect(row).to_have_count(1)
    expect(row).to_contain_text(payload["email"])
    expect(row).to_contain_text("tester")

    api_context.delete(f"/api/users/{created['id']}")


def test_api_deletion_is_reflected_in_the_ui(
    api_context: APIRequestContext, authenticated_page: Page
) -> None:
    assert api_context.delete("/api/users/2").status == 204

    authenticated_page.goto("/dashboard")
    authenticated_page.get_by_role("button", name="Load users").click()

    expect(authenticated_page.get_by_test_id("user-row")).to_have_count(4)
    expect(authenticated_page.get_by_text("Alan Turing")).to_have_count(0)


def test_bulk_setup_via_api_then_test_filtering(
    api_context: APIRequestContext, authenticated_page: Page
) -> None:
    """Create 10 users in about the time one form submission would take."""
    created_ids = []
    for _ in range(10):
        response = api_context.post("/api/users", data=new_user(role="dev"))
        created_ids.append(response.json()["id"])

    authenticated_page.goto("/dashboard")
    authenticated_page.get_by_role("button", name="Load users").click()
    expect(authenticated_page.get_by_test_id("user-row")).to_have_count(15)

    authenticated_page.get_by_label("Role").select_option("dev")
    expect(authenticated_page.get_by_test_id("user-row")).to_have_count(12)  # 2 seed + 10 new

    for user_id in created_ids:
        api_context.delete(f"/api/users/{user_id}")


def test_ui_state_matches_api_state(
    api_context: APIRequestContext, authenticated_page: Page
) -> None:
    """Cross-layer consistency check: the API is the source of truth, the UI
    must agree with it. Catches caching and pagination bugs."""
    api_users = api_context.get("/api/users").json()["data"]
    api_names = [u["name"] for u in api_users]

    authenticated_page.goto("/dashboard")
    authenticated_page.get_by_role("button", name="Load users").click()
    expect(authenticated_page.get_by_test_id("user-row")).to_have_count(len(api_names))

    ui_names = [
        text.strip()
        for text in authenticated_page.get_by_test_id("user-row")
        .locator("td:nth-child(2)")
        .all_inner_texts()
    ]
    assert ui_names == api_names
