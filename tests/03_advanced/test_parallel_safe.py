"""LESSON 10 -- Writing tests that survive `pytest -n auto` and CI sharding.

The four rules
--------------
1. No shared mutable state. Generate your own data; never assume record #3
   exists.
2. No ordering assumptions. Sharding will split your file across four machines;
   pytest-randomly would shuffle it. If test B needs test A, merge them.
3. Clean up what you create -- or better, use a reset hook (see the
   `reset_backend` fixture in tests/conftest.py).
4. Unique filenames/directories. `tmp_path` gives each test its own; a
   hard-coded /tmp/report.csv will collide under -n auto.

Run these four different ways and they must all pass:
    pytest tests/03_advanced/test_parallel_safe.py
    pytest tests/03_advanced/test_parallel_safe.py -n 4
    pytest tests/03_advanced/test_parallel_safe.py --splits 2 --group 1
    pytest tests/03_advanced/test_parallel_safe.py -p no:randomly
"""

import os

import pytest
from playwright.sync_api import APIRequestContext

from utils.data_factory import new_user, unique_suffix


@pytest.mark.api
@pytest.mark.parametrize("index", range(4))
def test_each_test_creates_its_own_user(api_context: APIRequestContext, index: int) -> None:
    payload = new_user()

    created = api_context.post("/api/users", data=payload)
    assert created.status == 201
    body = created.json()
    assert body["email"] == payload["email"]

    # Cleanup: leave the world as we found it.
    assert api_context.delete(f"/api/users/{body['id']}").status == 204


@pytest.mark.api
def test_data_is_unique_per_worker() -> None:
    worker = os.environ.get("PYTEST_XDIST_WORKER", "gw0 (serial run)")
    first, second = unique_suffix(), unique_suffix()

    assert first != second, "suffixes must be unique within a worker too"
    print(f"running on worker: {worker}")


@pytest.mark.api
def test_does_not_depend_on_seed_row_count(api_context: APIRequestContext) -> None:
    """BAD:  assert count == 5      (breaks the moment another test adds a row)
    GOOD: assert the thing you created is present."""
    payload = new_user(role="dev")
    created = api_context.post("/api/users", data=payload).json()

    listing = api_context.get("/api/users").json()
    emails = [u["email"] for u in listing["data"]]
    assert payload["email"] in emails

    api_context.delete(f"/api/users/{created['id']}")


def test_temp_files_are_per_test(tmp_path) -> None:
    """tmp_path is unique per test AND per worker -- no collisions under -n."""
    target = tmp_path / "output.csv"
    target.write_text("id,name\n1,test\n", encoding="utf-8")

    assert target.exists()
    # pytest names the directory after the test, so two tests can never collide
    # -- and neither can two xdist workers, which get separate parent dirs.
    assert "test_temp_files_are_per_test" in str(tmp_path)
