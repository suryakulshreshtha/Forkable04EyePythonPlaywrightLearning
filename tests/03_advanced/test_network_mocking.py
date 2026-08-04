"""LESSON 8 -- Network interception with page.route().

Why an SDET cares
-----------------
Some states are impossible or expensive to produce for real: a 500 from a
payment provider, a 10,000-row response, a field that is null only for accounts
created before 2019. Mocking lets you test the UI's handling of those states in
milliseconds, deterministically, with no backend cooperation.

The trade-off: a mocked test proves the UI handles a response shape. It does
NOT prove the backend still produces that shape. Pair every mocked test with a
contract/API test (see tests/04_api/) or you will ship a green suite against a
changed API.
"""

import json
import re

import pytest
from playwright.sync_api import Page, Route, expect


@pytest.fixture
def logged_in(page: Page) -> Page:
    page.goto("/")
    page.get_by_label("Username").fill("demo")
    page.get_by_label("Password").fill("Password123")
    page.get_by_role("button", name="Log in").click()
    expect(page).to_have_url(re.compile(r"/dashboard$"))
    return page


def test_stub_a_response_body(logged_in: Page) -> None:
    payload = {
        "count": 2,
        "data": [
            {
                "id": 99,
                "name": "Mocked Person",
                "email": "m@example.com",
                "role": "admin",
                "active": True,
            },
            {
                "id": 98,
                "name": "Second Mock",
                "email": "s@example.com",
                "role": "dev",
                "active": False,
            },
        ],
    }
    logged_in.route("**/api/users", lambda route: route.fulfill(json=payload))

    logged_in.get_by_role("button", name="Load users").click()

    expect(logged_in.get_by_test_id("user-row")).to_have_count(2)
    expect(logged_in.get_by_text("Mocked Person")).to_be_visible()


def test_empty_state_without_touching_the_database(logged_in: Page) -> None:
    logged_in.route("**/api/users", lambda route: route.fulfill(json={"count": 0, "data": []}))

    logged_in.get_by_role("button", name="Load users").click()
    expect(logged_in.get_by_test_id("table-status")).to_have_text("No users match your filter.")


def test_server_error_handling(logged_in: Page) -> None:
    """How does the UI behave on a 500? Almost nobody tests this. Do."""
    logged_in.route(
        "**/api/users",
        lambda route: route.fulfill(status=500, json={"error": "internal"}),
    )
    logged_in.get_by_role("button", name="Load users").click()

    # Our demo app has no error handling -- the table simply never appears.
    # Documenting the CURRENT behaviour is legitimate: this test will fail the
    # day someone adds a proper error banner, prompting an update. That is a
    # feature, not a nuisance.
    expect(logged_in.get_by_test_id("user-row")).to_have_count(0, timeout=5000)


def test_modify_a_real_response(logged_in: Page) -> None:
    """Let the request hit the server, then tamper with the reply.

    Great for "what if this optional field is missing" without inventing the
    entire payload by hand.
    """

    def strip_names(route: Route) -> None:
        response = route.fetch()
        body = response.json()
        for user in body["data"]:
            user["name"] = user["name"].upper()
        route.fulfill(response=response, body=json.dumps(body))

    logged_in.route("**/api/users", strip_names)
    logged_in.get_by_role("button", name="Load users").click()

    expect(logged_in.get_by_text("ADA LOVELACE")).to_be_visible()


def test_block_requests_to_measure_resilience(logged_in: Page) -> None:
    """Aborting is also how you speed suites up: block analytics, ads, fonts
    and third-party beacons that add seconds and flakiness to every page load.
    """
    logged_in.route("**/api/users", lambda route: route.abort("failed"))
    logged_in.get_by_role("button", name="Load users").click()

    expect(logged_in.get_by_role("table", name="Users")).to_be_hidden()


def test_assert_on_the_outgoing_request(logged_in: Page) -> None:
    captured = {}

    def capture(route: Route) -> None:
        captured["url"] = route.request.url
        captured["method"] = route.request.method
        route.continue_()

    logged_in.route("**/api/users*", capture)
    logged_in.get_by_role("button", name="Load users").click()
    expect(logged_in.get_by_test_id("user-row")).to_have_count(5)

    assert captured["method"] == "GET"
    assert captured["url"].endswith("/api/users")
