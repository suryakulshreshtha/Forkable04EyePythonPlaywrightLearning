"""In-memory JSON API for the bundled app.

Deliberately tiny. It exists so learners can practise:
  * pure API tests with Playwright's APIRequestContext (no browser at all)
  * hybrid tests: seed state over HTTP, then assert it in the UI
  * network mocking: stub these endpoints with page.route() and prove the UI
    renders whatever the backend claims

State is process-global, which is fine for a teaching app but is exactly the
kind of shared mutable state that makes real suites flaky -- see
docs/06-flaky-tests.md.
"""

from __future__ import annotations

from flask import Blueprint, jsonify, request

api_bp = Blueprint("api", __name__, url_prefix="/api")

SEED_USERS: list[dict] = [
    {"id": 1, "name": "Ada Lovelace", "email": "ada@example.com", "role": "admin", "active": True},
    {"id": 2, "name": "Alan Turing", "email": "alan@example.com", "role": "tester", "active": True},
    {
        "id": 3,
        "name": "Grace Hopper",
        "email": "grace@example.com",
        "role": "admin",
        "active": True,
    },
    {
        "id": 4,
        "name": "Edsger Dijkstra",
        "email": "edsger@example.com",
        "role": "dev",
        "active": False,
    },
    {
        "id": 5,
        "name": "Barbara Liskov",
        "email": "barbara@example.com",
        "role": "dev",
        "active": True,
    },
]

_users: list[dict] = [dict(u) for u in SEED_USERS]


def _next_id() -> int:
    return max((u["id"] for u in _users), default=0) + 1


@api_bp.get("/users")
def list_users():
    role = request.args.get("role")
    data = [u for u in _users if role is None or u["role"] == role]
    return jsonify({"count": len(data), "data": data})


@api_bp.get("/users/<int:user_id>")
def get_user(user_id: int):
    for user in _users:
        if user["id"] == user_id:
            return jsonify(user)
    return jsonify({"error": "user not found", "id": user_id}), 404


@api_bp.post("/users")
def create_user():
    payload = request.get_json(silent=True) or {}
    missing = [field for field in ("name", "email") if not payload.get(field)]
    if missing:
        return jsonify({"error": "missing required fields", "fields": missing}), 400

    user = {
        "id": _next_id(),
        "name": payload["name"],
        "email": payload["email"],
        "role": payload.get("role", "tester"),
        "active": bool(payload.get("active", True)),
    }
    _users.append(user)
    return jsonify(user), 201


@api_bp.put("/users/<int:user_id>")
def update_user(user_id: int):
    payload = request.get_json(silent=True) or {}
    for user in _users:
        if user["id"] == user_id:
            user.update(
                {k: v for k, v in payload.items() if k in {"name", "email", "role", "active"}}
            )
            return jsonify(user)
    return jsonify({"error": "user not found", "id": user_id}), 404


@api_bp.delete("/users/<int:user_id>")
def delete_user(user_id: int):
    global _users
    before = len(_users)
    _users = [u for u in _users if u["id"] != user_id]
    if len(_users) == before:
        return jsonify({"error": "user not found", "id": user_id}), 404
    return "", 204


@api_bp.post("/reset")
def reset_state():
    """Test hook: restore seed data.

    A dedicated reset endpoint is one of the highest-leverage things an SDET can
    ask a dev team for. It turns 'clean up after yourself' from a fragile
    teardown chain into one HTTP call.
    """
    global _users
    _users = [dict(u) for u in SEED_USERS]
    return jsonify({"reset": True, "count": len(_users)})
