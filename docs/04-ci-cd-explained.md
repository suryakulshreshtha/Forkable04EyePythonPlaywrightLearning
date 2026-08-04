# 04 — CI/CD explained, line by line

Open `.github/workflows/ci.yml` beside this page.

---

## Why CI at all

A test suite nobody runs is documentation. CI runs it on every change, on a machine that is not
yours, in a state you did not hand-craft. Everything below exists to make that fast enough that
people do not route around it.

---

## Anatomy of a workflow

```yaml
name: CI              # shown in the Actions tab and on badges
on: ...               # triggers
permissions: ...      # what the auto-generated token may do
concurrency: ...      # de-duplication
env: ...              # workflow-wide environment variables
jobs: ...             # the actual work
```

A **workflow** contains **jobs**; jobs run in parallel unless linked by `needs:`. Each job gets a
fresh VM. Each job contains **steps**, which run in order on that VM. Steps are either `run:`
(shell) or `uses:` (an action).

---

## Triggers

```yaml
on:
  push:
    branches: [main]
    paths-ignore: ["docs/**", "**.md", "LICENSE"]
  pull_request:
    branches: [main]
  workflow_dispatch:
```

- `push` to main — the post-merge safety net
- `pull_request` — the gate. Runs against a **merge commit** of your branch and the target, so you
  are testing what main will look like, not what your branch looks like
- `workflow_dispatch` — a manual **Run workflow** button
- `paths-ignore` — a README typo should not cost 24 runner-jobs

Other triggers worth knowing: `schedule` (see `nightly.yml`), `workflow_run` (see
`publish-report.yml`), `release`, `issue_comment`.

---

## Permissions — least privilege

```yaml
permissions:
  contents: read
  pull-requests: write
  checks: write
```

`GITHUB_TOKEN` is minted per run. Declare the narrowest set you need. A workflow that only runs
tests should not be able to push to your default branch. The `report` job re-declares its own
narrower block — job-level `permissions` overrides workflow-level.

---

## Concurrency — the cheapest saving available

```yaml
concurrency:
  group: ci-${{ github.workflow }}-${{ github.ref }}
  cancel-in-progress: true
```

Push three commits in two minutes and only the newest keeps running. Grouping by `github.ref`
means one branch's cancellation never touches another's.

Trade-off: you lose per-commit results. That matters for bisecting, which is why `nightly.yml`
sets `cancel-in-progress: false`.

---

## Job 1 — `lint`

```yaml
lint:
  runs-on: ubuntu-latest
  timeout-minutes: 10
```

`timeout-minutes` on every job. Without it, a hung browser burns six hours of your quota.

```yaml
- uses: actions/checkout@v4
- uses: ./.github/actions/setup-playwright
```

The second is our **composite action** — six steps (Python, pip cache, install, browser cache,
browser install, OS deps) collapsed into one line and reused by all four workflows.

```yaml
- run: ruff check --output-format=github .
```

`--output-format=github` emits `::error file=...,line=...` annotations, so lint problems appear
inline on the **Files changed** tab instead of buried in a log.

```yaml
- run: pytest --collect-only -q -m "not external"
```

Imports every test module without running it. Catches an import error, a bad fixture, or an
unregistered marker in ~5 seconds instead of eight minutes into the browser matrix.

```yaml
- run: python -m scripts.audit_locators
```

One layer deeper, and worth stealing for your own repo: it parses every `get_by_test_id` /
`get_by_label` / `get_by_role` literal out of the source with `ast`, renders the app with Flask's
test client, and checks each one still resolves — and that no label is ambiguous, which strict
mode would reject at runtime. No browser, ~0.2 seconds. A renamed `data-testid` fails in the first
40 seconds of the pipeline rather than the ninth minute.

The general principle: **push every check as early and as cheap as it will go.** Lint before
collect, collect before API, API before browsers, browsers before the report.

**Everything else `needs: lint`.** Fail fast, and fail cheap.

---

## Caching, in the composite action

```yaml
- uses: actions/setup-python@v5
  with:
    cache: pip
    cache-dependency-path: [requirements.txt, requirements-dev.txt]
```

Keyed on the hash of those files: change a dependency and the cache busts automatically.

```yaml
- id: pw
  run: echo "version=$(python -c '...playwright version...')" >> "$GITHUB_OUTPUT"

- uses: actions/cache@v4
  with:
    path: ~/.cache/ms-playwright
    key: pw-${{ runner.os }}-${{ steps.pw.outputs.version }}-${{ inputs.browser }}
```

Browser binaries are ~400 MB and 60–90s to download. The key includes the **resolved Playwright
version**, so upgrading the client always fetches matching binaries. A stale-browser/new-client
mismatch is a genuinely horrible bug to diagnose; this makes it impossible.

```yaml
- if: steps.pw-cache.outputs.cache-hit == 'true'
  run: python -m playwright install-deps
```

Even on a cache hit you must install the OS-level `.so` files — those live in `/usr/lib`, outside
the cached directory. Forgetting this is the single most common broken-CI-cache bug.

`$GITHUB_OUTPUT` is how a step publishes a value to later steps. `$GITHUB_ENV` sets an env var for
later steps in the same job. Both replaced the deprecated `::set-output`.

---

## Job 2 — `api-tests`

```yaml
- name: Start app under test
  run: |
    python -m app.server &
    echo "APP_PID=$!" >> "$GITHUB_ENV"

- name: Wait for app to be healthy
  run: python -m scripts.wait_for_app "$BASE_URL/health" 60
```

The **readiness probe** is not optional. Without it, pytest races the server, every test fails
with `ERR_CONNECTION_REFUSED`, and you spend an hour debugging your test code instead of your
startup ordering. Same idea as `wait-on`, `dockerize -wait`, or a Kubernetes readinessProbe.

```yaml
- run: pytest -m "api and not ui" --no-app -v
```

`--no-app` is our own flag telling the fixture "the workflow already started it, do not start your
own". `"api and not ui"` selects the genuinely browserless lane — see the marker discussion in
`conftest.py`.

This job takes about a minute. If the API contract is broken there is no point spending eight
minutes on UI tests.

---

## Job 3 — `ui-tests`, the matrix

```yaml
strategy:
  fail-fast: false
  matrix:
    browser: [chromium, firefox, webkit]
    python: ["3.12"]
    shard: [1, 2, 3, 4]
    include:
      - { browser: chromium, python: "3.10", shard: 1 }
      ...
```

3 × 1 × 4 = 12 jobs, plus 4 from `include` = **16 parallel jobs**.

- **`fail-fast: false`** — a WebKit failure must not cancel the Chromium legs. You want the whole
  picture from one run, not a game of whack-a-mole.
- **`include`** adds legs without multiplying the grid. A full 3-browser × 3-Python matrix is
  usually waste; one older-Python leg on one browser catches syntax and stdlib drift.

**Matrix vs shards — different jobs:**

| | What it does | Effect on wall clock |
| --- | --- | --- |
| Matrix | runs the *same* tests in *different* environments | none — more coverage |
| Shards | splits the *same* tests across machines | ~total ÷ shards |

```yaml
run: |
  MARKERS='not external and not visual'
  if [ "${{ github.event_name }}" = "pull_request" ]; then
    MARKERS="smoke and $MARKERS"
  fi
  pytest -m "$MARKERS" --browser ${{ matrix.browser }} \
         --splits 4 --group ${{ matrix.shard }} \
         --no-app --reruns 1 --reruns-delay 2
```

**Two-tier strategy:** PRs run `smoke` (fast merges); pushes to main run everything; the nightly
runs everything on every browser. Pick the tier by how much time you are willing to make a
reviewer wait.

`--splits/--group` is `pytest-split`. Each runner executes a quarter of the selected tests.

`--reruns 1` retries once. Read [06-flaky-tests.md](06-flaky-tests.md) before you increase it —
retries are a painkiller, not a cure.

```yaml
- uses: actions/upload-artifact@v4
  if: always()
  with:
    name: report-${{ matrix.browser }}-py${{ matrix.python }}-shard${{ matrix.shard }}
```

**`if: always()` is the most important line in the file.** Steps are skipped by default once a
previous step fails — which is exactly when you need the trace. And artifact names must be unique
per matrix leg, or the jobs overwrite each other.

---

## Job 4 — `external-tests`

```yaml
continue-on-error: true
```

The job runs, reports its result, and **cannot fail the workflow**. Correct for anything you do
not control: third-party sandboxes, public demo sites, shared staging.

Do not overuse it. A `continue-on-error` on your own test suite is a test suite you have chosen to
ignore.

---

## Job 5 — `report`

```yaml
needs: [api-tests, ui-tests]
if: always()
```

`needs` waits for them; `if: always()` runs even when they failed — a failure report is the one you
most want to read.

```yaml
- uses: actions/download-artifact@v4
  with:
    pattern: report-*
```

Collects all 17 artifacts, builds a single index page, and re-uploads it as `combined-report`
(which `publish-report.yml` then deploys to Pages).

**The PR comment** uses `actions/github-script@v7` — the GitHub REST API with a pre-authenticated
client. It looks for an existing comment starting with the same heading and *updates* it, so a
noisy branch gets one comment, not fourteen.

```yaml
- if: needs.ui-tests.result == 'failure' || needs.api-tests.result == 'failure'
  run: exit 1
```

Because this job is `if: always()`, it would otherwise report success and the whole workflow would
look green with failing tests underneath. This step is what makes the pipeline honest. `needs.<job>.result`
is one of `success`, `failure`, `cancelled`, `skipped`.

---

## `nightly.yml` — scheduled regression

```yaml
on:
  schedule:
    - cron: "0 2 * * *"
```

Cron is **UTC**, and GitHub's scheduler is best-effort — it can lag by minutes under load. Never
schedule anything time-critical on the hour.

Differences from the PR pipeline, and why:

- Full suite **minus `visual`**, not just smoke — nobody is waiting on it. Visual is excluded
  because a fork with no committed baselines fails on day one: Playwright generates the missing
  baseline and fails that run, by design. Left in, the auto-issue job would file a bug about it
  every morning. It gets its own `continue-on-error` job that uploads the baselines it generates.
- `-n 2` per browser, with **one app per xdist worker** (no `--no-app`), because a single
  in-memory app shared by two workers means their state resets fight each other
- `--reruns 2` — a lower bar for the unattended run
- `cancel-in-progress: false` — let it finish
- **Auto-files an issue on failure**, and comments on the existing one rather than opening a
  duplicate every night

An unattended pipeline that fails silently is not a pipeline.

---

## `manual-run.yml` — self-service

```yaml
on:
  workflow_dispatch:
    inputs:
      environment: { type: choice, options: [local, staging] }
      browser:     { type: choice, options: [chromium, firefox, webkit, all] }
      markers:     { type: string, default: "smoke" }
```

Typed inputs turn a pipeline into a tool the whole team can use. Types: `string`, `boolean`,
`choice`, `environment`.

```yaml
environment: ${{ inputs.environment }}
env:
  BASE_URL:      ${{ vars.BASE_URL || 'http://127.0.0.1:5000' }}
  TEST_PASSWORD: ${{ secrets.TEST_PASSWORD || 'Password123' }}
```

- **Variables** (`vars.*`) — non-sensitive, visible in logs
- **Secrets** (`secrets.*`) — masked in logs, unavailable to PRs from forks
- **Environments** — scope secrets *and* can require a human approval before the job starts. That
  is how you gate a production smoke run.

Secrets are masked, but base64 or reversing defeats the mask. The rule is simply: never print one.

```yaml
- run: echo "## Manual run finished" >> "$GITHUB_STEP_SUMMARY"
```

`$GITHUB_STEP_SUMMARY` renders markdown on the run's landing page. Cheap, and much friendlier than
asking people to read logs.

---

## `publish-report.yml` — Pages

```yaml
on:
  workflow_run:
    workflows: ["CI"]
    types: [completed]
```

Triggered **by another workflow**. This is the pattern when the publishing step needs permissions
the test job should not have — the test job stays `contents: read`, and only this one gets
`pages: write` and `id-token: write` (OIDC).

One-time setup: **Settings ▸ Pages ▸ Source: GitHub Actions**.

---

## Job 6 — `ci-gate`

```yaml
ci-gate:
  name: CI gate
  needs: [lint, api-tests, ui-tests]
  if: always()
```

One job whose only purpose is to have a **stable name**. Branch protection matches job names as
strings; matrix names contain the browser and shard (`UI webkit py3.12 shard 3/4`), so a rule
pinned to them breaks whenever the matrix changes — and GitHub will wait indefinitely for a check
that no longer exists.

`if: always()` plus an explicit `needs.<job>.result` comparison, for the same reason as the report
job: without the explicit check, an `always()` job reports success no matter what happened.

---

## Branch protection — where CI becomes a gate

Workflows only *report*. Protection rules *enforce*. In **Settings ▸ Branches ▸ Add rule** for
`main`:

- Require a pull request before merging
- Require status checks to pass: **`CI gate`** (one stable name — see the job above)
- Require branches to be up to date before merging
- Require review from Code Owners (pairs with `.github/CODEOWNERS`)
- Do not allow bypassing for administrators

Without this, a red pipeline is a suggestion.

---

## Dependabot

`.github/dependabot.yml` opens weekly PRs for pip packages and action versions, grouped so you get
one PR for "linters" rather than four. Your own CI then tests the upgrade for you — which is the
whole point of having it.

Review `playwright` bumps properly: client and browser binaries move together.

---

## Costs and etiquette

Public repos get free Actions minutes; private ones are metered, and matrix jobs multiply fast.
Levers, in order of impact:

1. `concurrency` + `cancel-in-progress`
2. `paths-ignore` for docs-only changes
3. Caching (pip + browsers)
4. Tiered suites — smoke on PRs, full on main, everything nightly
5. Sharding to cut wall clock (note: this *increases* total minutes while *reducing* waiting)
6. `timeout-minutes` so a hang cannot burn six hours

---

## Exercises

1. Break a test, open a PR, and follow the failure from the PR comment to the trace file.
2. Make WebKit run only on `main`, not on PRs.
3. Add a job that fails the build if `smoke` takes longer than 3 minutes.
4. Change the shard count from 4 to 8 and measure the difference in wall clock and total minutes.
5. Add a `staging` environment with a required reviewer and run `manual-run.yml` against it.
