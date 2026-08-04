# 03 — Fixtures, markers, and configuration

## Fixtures are dependency injection with a lifecycle

```python
@pytest.fixture
def thing():
    setup()
    yield value      # the test runs here
    teardown()       # runs even if the test failed
```

Ask for it by name in a test signature and pytest builds the graph for you.

### Scopes

| Scope | Created | Use for |
| --- | --- | --- |
| `function` (default) | per test | anything the test mutates |
| `class` | per class | rare |
| `module` | per file | expensive read-only setup |
| `session` | once | browser, API client, auth state |

Widen the scope only when the value is **immutable or reset between uses**. Session-scoped mutable
state is the classic route to a suite that passes serially and fails at `-n 4`.

### The fixtures in this repo

| Fixture | Scope | Purpose |
| --- | --- | --- |
| `base_url` | session | resolves the target URL; shifts port per xdist worker |
| `app_server` | session | starts/stops the bundled Flask app |
| `browser_context_args` | session | viewport, locale, timezone for every context |
| `configure_timeouts` | function | per-page timeouts, autouse |
| `api_context` | session | browserless HTTP client |
| `reset_backend` | function | restores seed data, autouse |
| `storage_state_path` | session | logs in once, saves cookies to disk |
| `authenticated_page` | function | fresh isolated page, already logged in |
| `login_page` / `dashboard_page` / `upload_page` | function | page objects |

Built-ins from `pytest-playwright` you get for free: `page`, `context`, `browser`,
`playwright`, `browser_name`, plus `tmp_path` and `request` from pytest.

```bash
pytest --fixtures        # every fixture with its docstring
```

### Autouse fixtures — the trap

`configure_timeouts` is autouse. If it had been written as:

```python
@pytest.fixture(autouse=True)
def configure_timeouts(page):    # ← WRONG
```

...then every API test would launch a browser, because requesting `page` builds it. Autouse
fixtures must never pull an expensive dependency unconditionally. Hence:

```python
if "page" not in request.fixturenames:
    yield
    return
```

### Autouse fixtures reach tests you forgot about

`reset_backend` is autouse and POSTs to the local app before every test. That is right for the UI
and API suites — and wrong for `tests/05_external/`, whose CI job never starts the local app.
Without a guard, every external test errors on `ConnectionRefused` before its body runs:

```python
if "no_reset" in request.keywords or "external" in request.keywords:
    yield
    return
```

The general rule: an autouse fixture applies to tests written months after you wrote it. Give it
an escape hatch, and key that hatch off a marker so opting out is visible in the test itself.

### Overriding fixtures

Define a fixture with the same name at a deeper level and yours wins. That is how this repo
overrides `base_url` and `browser_context_args` — the supported extension point, not a hack.

## Markers

```python
@pytest.mark.smoke
def test_valid_login(...): ...
```

```bash
pytest -m smoke
pytest -m "regression and not slow"
pytest -m "api and not ui"      # the truly browserless lane CI uses
```

Every marker is registered in `pytest.ini`, and `--strict-markers` turns a typo into an error
instead of a silently empty run.

They are also applied automatically by folder in `pytest_collection_modifyitems`
(`conftest.py`) — with an explicit marker on a module always winning over the automatic one.

**Smoke-suite discipline:** smoke is what gates every PR, so it must stay under a few minutes.
Ours covers login, dashboard load, API list, CRUD, and auth reuse. If everything is smoke, nothing
is — and your team starts merging on red.

## Parametrize

```python
@pytest.mark.parametrize(
    "case", login_cases("invalid_logins"),
    ids=lambda c: c["case"].replace(" ", "-"),
)
def test_invalid_logins_are_rejected(login_page, case): ...
```

Each case is a separate test with its own result. `ids=` is not cosmetic — it is the difference
between a CI failure reading `[empty-password]` and `[case2]`.

Data lives in `test-data/users.json`, so adding a case is a JSON edit, not a code edit.

## Configuration precedence

```
CLI flag  >  environment variable  >  .env file  >  default in utils/config.py
```

```bash
pytest --base-url https://staging.example.com
BASE_URL=https://staging.example.com pytest
```

No test in this repo contains a URL, username, or password. That is what lets the same suite run
against local, CI, and staging with nothing but env vars changing.

## Exercises

1. Add an `admin_page` fixture with its own storage state.
2. Add a `perf` marker that runs in neither smoke nor regression.
3. Run `pytest --setup-plan tests/02_pom/test_login.py` and read the fixture graph.
