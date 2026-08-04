"""LESSON 12 -- API testing with Playwright's APIRequestContext.

No browser is launched here. These tests run in milliseconds, which is why the
CI pipeline runs them first: if the API contract is broken, there is no point
spending eight minutes on UI tests.

Testing-pyramid reality check for an SDET: if a rule can be verified at the API
layer, verify it there. Reserve UI tests for things that only exist in the UI --
rendering, navigation, client-side validation, accessibility.
"""

import pytest
from playwright.sync_api import APIRequestContext

from utils.data_factory import new_user


@pytest.mark.smoke
def test_list_users(api_context: APIRequestContext) -> None:
    response = api_context.get("/api/users")

    assert response.ok
    assert response.status == 200
    body = response.json()
    assert body["count"] == 5
    assert {u["role"] for u in body["data"]} == {"admin", "tester", "dev"}


def test_query_parameter_filtering(api_context: APIRequestContext) -> None:
    response = api_context.get("/api/users", params={"role": "admin"})

    body = response.json()
    assert body["count"] == 2
    assert all(u["role"] == "admin" for u in body["data"])


def test_get_single_user(api_context: APIRequestContext) -> None:
    user = api_context.get("/api/users/1").json()

    assert user["name"] == "Ada Lovelace"
    assert user["email"] == "ada@example.com"


def test_404_for_unknown_user(api_context: APIRequestContext) -> None:
    response = api_context.get("/api/users/9999")

    assert response.status == 404
    assert response.json()["error"] == "user not found"


@pytest.mark.smoke
def test_create_read_update_delete(api_context: APIRequestContext) -> None:
    """One test covering the full lifecycle.

    Splitting CRUD into four tests that share an ID is the classic ordering
    trap -- it breaks under parallelism. Keep a lifecycle in one test.
    """
    payload = new_user(role="dev")

    # CREATE
    created = api_context.post("/api/users", data=payload)
    assert created.status == 201
    user = created.json()
    user_id = user["id"]
    assert user["name"] == payload["name"]

    # READ
    fetched = api_context.get(f"/api/users/{user_id}").json()
    assert fetched == user

    # UPDATE
    updated = api_context.put(f"/api/users/{user_id}", data={"role": "admin", "active": False})
    assert updated.status == 200
    assert updated.json()["role"] == "admin"
    assert updated.json()["active"] is False

    # DELETE
    assert api_context.delete(f"/api/users/{user_id}").status == 204
    assert api_context.get(f"/api/users/{user_id}").status == 404


@pytest.mark.parametrize(
    ("payload", "missing"),
    [
        ({}, ["name", "email"]),
        ({"name": "No Email"}, ["email"]),
        ({"email": "no-name@example.com"}, ["name"]),
    ],
)
def test_validation_errors(
    api_context: APIRequestContext, payload: dict, missing: list[str]
) -> None:
    response = api_context.post("/api/users", data=payload)

    assert response.status == 400
    assert response.json()["fields"] == missing


def test_response_headers(api_context: APIRequestContext) -> None:
    response = api_context.get("/api/users")

    assert response.ok
    assert response.headers["content-type"].startswith("application/json")

    # Deliberately NO latency assertion here. A response-time budget on a
    # shared CI runner is the most reliable way to manufacture a flaky test,
    # and a flaky test gets deleted -- after which you have no coverage at all.
    # Measure performance with a tool built for it, not with an assert.
