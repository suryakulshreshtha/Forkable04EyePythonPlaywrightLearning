"""Root conftest -- fixtures and hooks available to the whole suite.

Read this file top to bottom once; it is where most of the "how does the
framework actually work" knowledge lives.

Fixture layering used in this repo:
    conftest.py                (here)  -> global config, app lifecycle, hooks
    tests/conftest.py                  -> auth/session fixtures shared by tests
    tests/02_pom/conftest.py           -> page-object fixtures
That layering is a pytest feature, not a convention: a conftest applies to its
directory and everything below it.
"""

from __future__ import annotations

import os
import socket
import subprocess
import sys
import time
from pathlib import Path

import pytest

from utils.config import settings
from utils.logger import get_logger, log_group

log = get_logger("conftest")

ROOT = Path(__file__).resolve().parent


# ---------------------------------------------------------------------------
# CLI options
# ---------------------------------------------------------------------------
def pytest_addoption(parser: pytest.Parser) -> None:
    """Custom flags:  pytest --env=ci --no-app"""
    group = parser.getgroup("forkable04eye")
    group.addoption(
        "--env",
        action="store",
        default=os.environ.get("ENV", "local"),
        choices=["local", "ci", "staging"],
        help="Logical environment to target.",
    )
    group.addoption(
        "--no-app",
        action="store_true",
        default=False,
        help="Do not auto-start the bundled Flask app (use when CI already started it).",
    )


# ---------------------------------------------------------------------------
# Session-wide configuration
# ---------------------------------------------------------------------------
@pytest.fixture(scope="session")
def worker_id(request: pytest.FixtureRequest) -> str:
    """'master' when running serially, 'gw0'/'gw1'/... under pytest-xdist."""
    return getattr(request.config, "workerinput", {}).get("workerid", "master")


@pytest.fixture(scope="session")
def base_url(pytestconfig: pytest.Config, worker_id: str) -> str:
    """Overrides the fixture from pytest-base-url.

    Because pytest-playwright consumes `base_url`, every `page.goto("/login")`
    with a relative path resolves against this automatically.

    ONE APP INSTANCE PER XDIST WORKER
    ---------------------------------
    Our demo app keeps state in memory, and the `reset_backend` fixture wipes
    that state before each test. Point four workers at ONE app and worker gw2's
    reset destroys the row gw0 just created -- a textbook shared-state race.

    Two ways out, and you will meet both in real jobs:
      (a) isolate the environment per worker  <- what we do here (port + N)
      (b) isolate the DATA per worker (unique accounts/tenants) against one
          shared environment  <- what you usually must do at work, because you
          rarely get to spin up N copies of a real system

    tests/03_advanced/test_parallel_safe.py demonstrates (b).
    """
    explicit = pytestconfig.getoption("--base-url")
    if explicit:
        return explicit

    url = settings.base_url
    # --no-app means an external process owns the app; we must not shift ports.
    if pytestconfig.getoption("--no-app") or worker_id == "master":
        return url

    offset = int(worker_id.removeprefix("gw") or 0)
    host, _, port = url.rpartition(":")
    return f"{host}:{int(port) + offset}"


@pytest.fixture(scope="session", autouse=True)
def announce_configuration(base_url: str) -> None:
    with log_group("Test configuration"):
        for key, value in {**settings.masked(), "resolved_base_url": base_url}.items():
            print(f"  {key:>18}: {value}")


# ---------------------------------------------------------------------------
# App lifecycle
# ---------------------------------------------------------------------------
def _port_open(host: str, port: int, timeout: float = 0.5) -> bool:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.settimeout(timeout)
        return sock.connect_ex((host, port)) == 0


@pytest.fixture(scope="session", autouse=True)
def app_server(pytestconfig: pytest.Config, base_url: str):
    """Start the bundled app if nothing is already listening.

    Locally this means `pytest` just works with no second terminal.
    In CI we pass --no-app because the workflow starts the app itself, so the
    workflow log shows the startup and the readiness probe as separate steps.
    """
    if pytestconfig.getoption("--no-app") or not base_url.startswith(
        ("http://127.0.0.1", "http://localhost")
    ):
        yield None
        return

    host = "127.0.0.1"
    port = int(base_url.rsplit(":", 1)[-1].split("/")[0])

    if _port_open(host, port):
        log.info("app already running on %s:%s -- reusing it", host, port)
        yield None
        return

    log.info("starting bundled app on %s:%s", host, port)
    process = subprocess.Popen(
        [sys.executable, "-m", "app.server"],
        cwd=str(ROOT),
        env={**os.environ, "FLASK_HOST": host, "FLASK_PORT": str(port)},
        stdout=subprocess.DEVNULL,
        stderr=subprocess.STDOUT,
    )

    deadline = time.time() + 30
    while time.time() < deadline:
        if _port_open(host, port):
            break
        if process.poll() is not None:
            raise RuntimeError("app process died during startup -- run `make app` to see why")
        time.sleep(0.3)
    else:
        process.terminate()
        raise RuntimeError(f"app did not start on {host}:{port} within 30s")

    yield process

    log.info("stopping bundled app")
    process.terminate()
    try:
        process.wait(timeout=5)
    except subprocess.TimeoutExpired:  # pragma: no cover
        process.kill()


# ---------------------------------------------------------------------------
# Playwright fixture overrides
# ---------------------------------------------------------------------------
@pytest.fixture(scope="session")
def browser_context_args(browser_context_args: dict, base_url: str) -> dict:
    """Applies to EVERY context, so every test gets consistent settings.

    Overriding this fixture is the supported way to configure viewport, locale,
    permissions, HTTP credentials, recording, etc. across the suite.
    """
    return {
        **browser_context_args,
        "base_url": base_url,
        "viewport": {"width": 1440, "height": 900},
        "locale": "en-GB",
        "timezone_id": "Europe/London",
        "ignore_https_errors": True,
        # Freezing the reduced-motion preference makes animations instant,
        # which removes a whole class of screenshot flakiness.
        "reduced_motion": "reduce",
    }


@pytest.fixture(autouse=True)
def configure_timeouts(request):
    """One place to tune waiting.

    Default action timeout is 30s in Playwright. Shorter is usually better: a
    test that is going to fail should fail fast so CI feedback stays quick.

    Note the `request.fixturenames` guard. If this fixture simply took `page`
    as an argument, being autouse would force a BROWSER TO LAUNCH for every
    API test too -- turning a 40ms test into a 2-second one. Autouse fixtures
    must never pull in expensive dependencies unconditionally.
    """
    if "page" not in request.fixturenames:
        yield
        return

    page = request.getfixturevalue("page")
    page.set_default_timeout(settings.default_timeout_ms)
    page.set_default_navigation_timeout(settings.default_timeout_ms * 2)
    yield


# ---------------------------------------------------------------------------
# Hooks
# ---------------------------------------------------------------------------
def pytest_collection_modifyitems(config: pytest.Config, items: list[pytest.Item]) -> None:
    """Auto-mark tests by folder, so nobody forgets a marker.

    tests/04_api/... gets `api`, tests/05_external/... gets `external`, and
    anything not already marked `smoke` is treated as `regression`.

    A module can still opt in explicitly -- see tests/04_api/test_api_ui_hybrid.py,
    which sets `pytestmark = pytest.mark.ui` because it does launch a browser.
    That is why the browserless CI lane selects `-m "api and not ui"` rather
    than just `-m api`.
    """
    for item in items:
        path = str(item.fspath)
        already = {m.name for m in item.iter_markers()}

        if f"{os.sep}04_api{os.sep}" in path:
            item.add_marker(pytest.mark.api)
        elif f"{os.sep}05_external{os.sep}" in path:
            item.add_marker(pytest.mark.external)
        elif not already & {"ui", "api"}:
            # Only default to `ui` when the test has not already declared what
            # it is. Explicit beats implicit -- a hook that overwrites a
            # deliberate marker is worse than no hook at all.
            item.add_marker(pytest.mark.ui)

        if not any(m.name == "smoke" for m in item.iter_markers()):
            item.add_marker(pytest.mark.regression)


@pytest.hookimpl(hookwrapper=True, tryfirst=True)
def pytest_runtest_makereport(item, call):
    """Stash each phase's result on the item.

    This is the canonical recipe that lets a fixture ask "did the test I just
    ran actually fail?" during teardown -- used below for failure annotations.
    """
    outcome = yield
    report = outcome.get_result()
    setattr(item, f"rep_{report.when}", report)


@pytest.fixture(autouse=True)
def annotate_failures(request):
    """Emit a GitHub Actions error annotation for each failed test.

    Result: the failure shows up inline on the PR's Files-changed view instead
    of being buried in the raw log. Costs three lines; enormous quality-of-life
    win for reviewers.
    """
    yield
    report = getattr(request.node, "rep_call", None)
    if report is not None and report.failed and os.environ.get("GITHUB_ACTIONS") == "true":
        file_path = Path(str(request.node.fspath)).relative_to(ROOT)
        line = request.node.location[1] + 1
        title = request.node.name
        print(
            f"::error file={file_path},line={line},title=Test failed: {title}::{report.longreprtext[:600]}"
        )
