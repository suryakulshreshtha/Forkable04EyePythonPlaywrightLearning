# Forkable04EyePythonPlaywrightLearning

[![CI](https://github.com/suryakulshreshtha/Forkable04EyePythonPlaywrightLearning/actions/workflows/ci.yml/badge.svg)](https://github.com/suryakulshreshtha/Forkable04EyePythonPlaywrightLearning/actions/workflows/ci.yml)
[![Nightly](https://github.com/suryakulshreshtha/Forkable04EyePythonPlaywrightLearning/actions/workflows/nightly.yml/badge.svg)](https://github.com/suryakulshreshtha/Forkable04EyePythonPlaywrightLearning/actions/workflows/nightly.yml)
[![Python 3.10+](https://img.shields.io/badge/python-3.10%2B-blue)](https://www.python.org/)
[![Playwright](https://img.shields.io/badge/playwright-1.47-green)](https://playwright.dev/python/)
[![License: MIT](https://img.shields.io/badge/license-MIT-lightgrey)](LICENSE)

> **Fork it, run it, break it, fix it.** A complete Python + Playwright test framework that teaches
> both the automation *and* the CI/CD around it — the half most tutorials skip.

Everything here runs against a **bundled Flask app** that ships in the repo, so a fresh fork is green
in about two minutes with no accounts, keys, or external services. A handful of tests deliberately hit
real public sites so you can see how differently those behave.

---

## What you will learn

**Playwright**

- Locators that survive a redesign — `get_by_role` / `get_by_label` / `get_by_test_id`, and why XPath is last
- Web-first assertions and auto-waiting (and why `time.sleep()` is banned here)
- Forms, dropdowns, checkboxes, file upload from disk *and* from memory, downloads
- Network interception: stub a 500, an empty list, or a mangled payload in milliseconds
- Storage state — log in once per session instead of 200 times
- API testing with `APIRequestContext`, plus hybrid "seed over HTTP, assert in the UI" tests
- Visual regression, with an honest account of when it is worth the flakiness

**Framework design**

- Page Object Model, component objects, and where POM starts to rot
- Fixture layering across three `conftest.py` files
- Markers, data-driven `parametrize`, and environment-driven config
- Writing tests that survive `-n auto` and four-way CI sharding

**CI/CD**

- A four-stage pipeline: lint → API tests → UI matrix → merged report
- Matrix builds, sharding, dependency + browser caching, artifacts, traces
- Scheduled nightlies that file their own issue when they break
- `workflow_dispatch` inputs, environments, secrets, and least-privilege tokens
- Publishing HTML reports to GitHub Pages, PR comments, failure annotations
- Dependabot, pre-commit, CODEOWNERS, branch protection

---

## 60-second quickstart

**Option A — GitHub Codespaces (nothing to install)**

Click **Code ▸ Codespaces ▸ Create codespace**. The devcontainer installs everything, then:

```bash
make smoke
```

**Option B — locally**

```bash
git clone https://github.com/suryakulshreshtha/Forkable04EyePythonPlaywrightLearning.git
cd Forkable04EyePythonPlaywrightLearning

python -m venv .venv && source .venv/bin/activate    # Windows: .venv\Scripts\activate
make install          # deps + browser binaries

make test             # everything except the public-internet tests
```

You do **not** need to start the app yourself. The `app_server` fixture in `conftest.py` starts it
if nothing is already listening on the port, and stops it afterwards.

**Option C — Docker**

```bash
docker compose up --build --abort-on-container-exit
```

---

## Repo tour

```
app/          The Flask app under test. Login, a dynamically loaded table,
              upload/download, a deliberately slow page, and a JSON API.
pages/        Page objects + a component object for the nav bar.
tests/
  01_basics/  Heavily commented lessons: first test, locators, assertions,
              forms/upload, waiting.
  02_pom/     The same coverage rewritten with page objects and fixtures.
  03_advanced/Network mocking, storage state, parallel safety, visual.
  04_api/     Browserless API tests, and API-setup + UI-assert hybrids.
  05_external/Real public sites. Marked `external`, never blocks a merge.
utils/        Config, logging, Faker-based data factory.
scripts/      Readiness probe used by CI and docker-compose.
.github/      Four workflows, a composite action, Dependabot, templates.
docs/         The written course. Start with docs/LEARNING_PATH.md.
```

Three `conftest.py` files, deliberately:

| File | Scope | Holds |
| --- | --- | --- |
| `conftest.py` | everything | CLI options, app lifecycle, Playwright overrides, hooks |
| `tests/conftest.py` | all tests | API context, backend reset, auth/storage state |
| `tests/02_pom/conftest.py` | POM tests | page-object fixtures |

---

## Learning path

Work through `docs/` in order — each page is short and ends with exercises.

| Day | Read | Then run |
| --- | --- | --- |
| 1 | [00-setup.md](docs/00-setup.md) | `make install && make smoke` |
| 2 | [01-playwright-basics.md](docs/01-playwright-basics.md) | `pytest tests/01_basics -v --headed` |
| 3 | [02-page-object-model.md](docs/02-page-object-model.md) | `pytest tests/02_pom -v` |
| 4 | [03-fixtures-and-markers.md](docs/03-fixtures-and-markers.md) | `pytest --fixtures \| less` |
| 5 | [04-ci-cd-explained.md](docs/04-ci-cd-explained.md) | open a PR in your fork and watch it |
| 6 | [05-debugging-traces.md](docs/05-debugging-traces.md) | `make debug`, then `make trace` |
| 7 | [06-flaky-tests.md](docs/06-flaky-tests.md) | `pytest -m regression -n auto` twice |

Full track with exercises: **[docs/LEARNING_PATH.md](docs/LEARNING_PATH.md)**

---

## Running tests

```bash
make test                 # everything except `external`
make smoke                # the PR gate: fast critical path
make api                  # browserless, ~1 second
make parallel             # -n auto
make headed               # watch it drive the browser
make debug                # Playwright Inspector, step by step
make audit                # static locator check, no browser, ~0.2s
make visual               # run visual tests locally and regenerate baselines

pytest -m "smoke and not slow"                 # marker expressions
pytest tests/02_pom/test_login.py::test_valid_login
pytest -k "filter or search"                   # match by name
pytest --browser firefox --browser webkit      # multiple engines in one run
pytest --splits 4 --group 2                    # what one CI shard runs
pytest --base-url https://staging.example.com  # point anywhere
pytest --last-failed                           # rerun only what broke
```

Markers: `smoke`, `regression`, `api`, `ui`, `external`, `visual`, `slow`.
They are auto-applied by folder in `pytest_collection_modifyitems` — read that hook, it is short.

---

## Reading the CI pipeline

```
 push / pull_request
         │
      ┌──▼──┐   ruff + black + pytest --collect-only        ~40s
      │lint │   fails fast so a typo never costs 20 runner-minutes
      └──┬──┘
         ├──────────────┬────────────────────────┐
   ┌─────▼─────┐  ┌─────▼──────────────────┐  ┌──▼───────────────┐
   │ api-tests │  │ ui-tests               │  │ external-tests   │
   │ no browser│  │ 3 browsers × 4 shards  │  │ continue-on-error│
   │   ~1 min  │  │ + a python 3.10 leg    │  │ never blocks     │
   └─────┬─────┘  └─────┬──────────────────┘  └──────────────────┘
         └──────┬───────┘
           ┌────▼────┐  merge shard reports → artifact → Pages
           │ report  │  → PR comment → fail the run if anything was red
           └─────────┘
```

Every construct in there is explained line by line in
**[docs/04-ci-cd-explained.md](docs/04-ci-cd-explained.md)**.

Concept map:

| Concept | Where to look |
| --- | --- |
| Fail-fast static gate | `ci.yml` → lint job: ruff, black, `--collect-only`, locator audit |
| Job dependencies, fail-fast ordering | `ci.yml` → `needs:` |
| Matrix + `include` for an extra leg | `ci.yml` → `strategy.matrix` |
| Sharding | `ci.yml` → `--splits 4 --group ${{ matrix.shard }}` |
| Caching pip and browser binaries | `.github/actions/setup-playwright/action.yml` |
| Service startup + readiness probe | `ci.yml` → "Start app" / "Wait for app" |
| Artifacts, traces, videos | `ci.yml` → `upload-artifact` with `if: always()` |
| Concurrency / auto-cancel | `ci.yml` → `concurrency:` |
| Least-privilege token | `ci.yml` → `permissions:` |
| Scheduled run + auto-filed issue | `nightly.yml` |
| Manual run with typed inputs | `manual-run.yml` |
| Secrets, variables, environments | `manual-run.yml` |
| Publishing to Pages via `workflow_run` | `publish-report.yml` |
| Reusable composite action | `.github/actions/setup-playwright/` |
| Shift-left (same gate locally) | `.pre-commit-config.yaml`, `Makefile` |

---

## Reports and traces

- **CI**: every job uploads a `report-*` artifact. Download it, unzip, open `report.html`.
- **Pages**: after enabling Pages, the merged report lands at
  `https://suryakulshreshtha.github.io/Forkable04EyePythonPlaywrightLearning/`
- **Traces** are the real prize. A trace is a recording of the run — DOM snapshot at every step,
  network log, console, screenshots:

```bash
playwright show-trace reports/test-results/<test-name>/trace.zip
# or just:
make trace
```

Traces are captured `retain-on-failure`, so a green run costs nothing.

---

## Upload and CI/CD runbook

Terminal-ready, start to finish: **[UPLOAD_STEPS.md](UPLOAD_STEPS.md)** — local check, commit
history, repo creation, authentication, Pages, branch protection, and a scripted demo that proves
the pipeline blocks a bad merge. Every step has a **without `gh`** path, and there is a
troubleshooting table for the errors people actually hit.

## After you fork — one-time setup

1. **Settings ▸ Pages** → Source: **GitHub Actions** (enables the published report)
2. **Settings ▸ Branches** → protect `main`: require the single **`CI gate`** status check
3. ~~Edit `.github/CODEOWNERS`~~ — already set to `@suryakulshreshtha`
4. ~~Replace the badge URLs~~ — already pointed at `suryakulshreshtha`
5. Optional: **Settings ▸ Secrets and variables ▸ Actions** → add `TEST_PASSWORD` to try the
   secrets path in `manual-run.yml`
6. `pre-commit install` locally so you get the same lint gate before you push

> **Why one required check and not sixteen?** Matrix job names contain the browser and shard
> number (`UI webkit py3.12 shard 3/4`), so a protection rule pinned to them breaks the moment you
> change the matrix — and GitHub will happily wait forever for a check that no longer exists. The
> `ci-gate` job aggregates `lint`, `api-tests` and `ui-tests` under one stable name. Require that.

> **Visual tests ship with no baselines**, deliberately: screenshots must be generated on the CI
> runner's OS, not your laptop. The nightly's `visual-suite` job is `continue-on-error` and uploads
> the baselines it generates. Download that artifact, inspect every PNG, commit them under
> `tests/**/__snapshots__/`, then flip `continue-on-error: false` to make it a real gate.

---

## Exercises

Each lesson file ends with a `YOUR TURN` block. Worked solutions live in
[`docs/solutions/`](docs/solutions/) — try it yourself first.

---

## Troubleshooting

| Symptom | Fix |
| --- | --- |
| `Executable doesn't exist at .../chrome-linux/chrome` | `python -m playwright install --with-deps` |
| `Host system is missing dependencies` | `sudo python -m playwright install-deps`, or use Docker/Codespaces |
| macOS: 403s, wrong page title, `Locator.fill` timeouts | **AirPlay Receiver owns port 5000.** Turn it off in System Settings ▸ General ▸ AirDrop & Handoff, or run `BASE_URL=http://127.0.0.1:5001 FLASK_PORT=5001 pytest` |
| `ERR_CONNECTION_REFUSED` | Something else is on port 5000, or you passed `--no-app` without starting the app |
| A locator silently stopped matching | `make audit` — tells you which literal broke, in 0.2s |
| `strict mode violation: resolved to N elements` | Your locator is ambiguous — scope it or `.filter()` it. This is Playwright helping. |
| A test passes alone but fails in the suite | Order/data dependency. See [docs/06-flaky-tests.md](docs/06-flaky-tests.md). |
| Visual tests fail on a fresh clone | Baselines are generated on the CI OS. `pytest -m visual --update-snapshots` locally. |
| `Marker not registered` | Add it to `pytest.ini` — `--strict-markers` is on deliberately. |

---

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md). Short version: no `sleep`, no hard-coded credentials,
no test that depends on another test, and prove your test fails when the feature is broken.

## License

MIT — see [LICENSE](LICENSE). Use it for training, workshops, or interview prep.
