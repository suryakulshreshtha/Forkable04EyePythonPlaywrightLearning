# 00 — Setup

## Prerequisites

- Python 3.10 or newer (`python --version`)
- Git
- ~500 MB free for browser binaries

## Install

```bash
python -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate
pip install -r requirements-dev.txt
python -m playwright install --with-deps
pre-commit install                 # optional but recommended
```

`make install` does all of that in one go.

### What `playwright install` actually does

It downloads *patched* builds of Chromium, Firefox and WebKit into `~/.cache/ms-playwright`
(`%USERPROFILE%\AppData\Local\ms-playwright` on Windows). These are not your system browsers, which
is the point: everyone on the team and every CI runner drives byte-identical binaries.

`--with-deps` also installs the OS-level shared libraries the browsers need. On Linux that requires
sudo, which is why CI uses either `--with-deps` on a fresh runner or the official Playwright Docker
image.

Pin discipline: the Python `playwright` package version and the browser binaries are a matched pair.
After any upgrade, run `playwright install` again. Our CI cache key includes the resolved Playwright
version precisely so an upgrade cannot silently reuse old binaries.

## Verify

```bash
make check      # lint + import every test module without running anything
make api        # browserless, should take about a second
make smoke      # launches a real browser
```

If `make api` passes but `make smoke` fails, the problem is browsers/OS libraries, not your code.

## Configuration

Nothing is hard-coded. `utils/config.py` reads environment variables with sensible defaults:

| Variable | Default | Meaning |
| --- | --- | --- |
| `ENV` | `local` | Logical environment name |
| `BASE_URL` | `http://127.0.0.1:5000` | Where the app under test lives |
| `TEST_USER` | `demo` | Login username |
| `TEST_PASSWORD` | `Password123` | Login password |
| `HEADLESS` | `true` | Headless browsers |
| `DEFAULT_TIMEOUT_MS` | `10000` | Per-action timeout |
| `LOG_LEVEL` | `INFO` | Logger verbosity |

```bash
cp .env.example .env      # .env is gitignored
```

In CI these come from workflow `env:`, repository **variables**, and repository **secrets** —
never from a committed file. That separation is the whole reason `config.py` exists.

## macOS: port 5000 is not free

AirPlay Receiver binds `127.0.0.1:5000` on macOS and answers every request with
**403**. If your tests point there you get a page of failures that look like
product bugs — wrong page title, `Locator.fill` timeouts, `403` where the API
should return `201`.

The `app_server` fixture now detects this and stops with an explanation rather
than letting you debug a phantom. See what holds the port:

```bash
lsof -nP -iTCP:5000 -sTCP:LISTEN
```

Two fixes:

1. System Settings ▸ General ▸ AirDrop & Handoff ▸ **AirPlay Receiver: Off**
2. Use another port:

```bash
BASE_URL=http://127.0.0.1:5001 FLASK_PORT=5001 pytest
```

The general lesson is worth more than the workaround: **"the port is open" is
not "my service is running."** A readiness probe must identify the service, not
just complete a TCP handshake — which is exactly why `scripts/wait_for_app.py`
checks `/health` rather than opening a socket.

## Running the app manually

```bash
make app     # http://127.0.0.1:5000  (demo / Password123)
```

You rarely need to: the `app_server` fixture starts it automatically if the port is free, and
reuses your instance if it is already running.

## IDE

VS Code users get the recommended extensions automatically via `.devcontainer/devcontainer.json`.
The **Playwright Test for VS Code** extension gives you run-on-click, breakpoints, and a locator
picker; the **Ruff** extension gives you the CI lint result as you type.
