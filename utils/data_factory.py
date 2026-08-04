"""Faker-backed test data.

Why not fixtures files full of "test1@test.com"?
------------------------------------------------
Hard-coded data collides the moment you run tests in parallel or run the same
suite twice against a persistent environment. Generated, uniquely-suffixed data
is the cheapest route to parallel-safe tests. See tests/03_advanced/
test_parallel_safe.py.
"""

from __future__ import annotations

import itertools
import json
import os
import time
from pathlib import Path

from faker import Faker

fake = Faker()
Faker.seed(int(os.environ.get("FAKER_SEED", "0")) or None)

DATA_DIR = Path(__file__).resolve().parent.parent / "test-data"


_counter = itertools.count(1)


def unique_suffix() -> str:
    """Unique per worker AND per call -- safe under pytest-xdist.

    Note the counter. A timestamp alone is NOT enough: two calls inside the
    same millisecond produce the same value, and modern machines execute a lot
    inside one millisecond. This is exactly the kind of "works on my laptop,
    collides on the CI runner" bug that makes people blame flakiness on
    Playwright.
    """
    worker = os.environ.get("PYTEST_XDIST_WORKER", "gw0")
    return f"{worker}-{int(time.time() * 1000) % 1_000_000}-{next(_counter)}"


def new_user(role: str = "tester", active: bool = True) -> dict:
    suffix = unique_suffix()
    return {
        "name": f"{fake.first_name()} {fake.last_name()} {suffix}",
        "email": f"user-{suffix}@example.com",
        "role": role,
        "active": active,
    }


def load_json(filename: str) -> dict:
    return json.loads((DATA_DIR / filename).read_text(encoding="utf-8"))


def login_cases(kind: str) -> list[dict]:
    """Feed pytest.mark.parametrize from a JSON file -- data-driven testing."""
    return load_json("users.json")[kind]
