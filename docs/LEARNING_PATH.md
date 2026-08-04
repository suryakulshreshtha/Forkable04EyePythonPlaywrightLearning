# The 7-day learning path

One focused hour a day. Read, run, then do the exercise. Do not skip the exercises — reading
automation code feels productive and teaches almost nothing.

---

## Day 1 — Setup and orientation

**Read:** [00-setup.md](00-setup.md)

```bash
make install
make smoke          # should be green in ~30 seconds
make app            # then open http://127.0.0.1:5000 and click around
```

Poke the app manually first. You cannot automate what you have not used.

**Checkpoint:** you can explain what `make smoke` selected and why it was faster than `make test`.

---

## Day 2 — Playwright fundamentals

**Read:** [01-playwright-basics.md](01-playwright-basics.md)
**Code:** `tests/01_basics/` — five files, read them in order.

```bash
pytest tests/01_basics -v
pytest tests/01_basics/test_02_locators.py --headed --slowmo 700
```

**Exercises 1–5** are at the bottom of each lesson file.

**Checkpoint:** you can say, without looking, why `expect(loc).to_have_text("x")` is safer than
`assert loc.inner_text() == "x"`.

---

## Day 3 — Page Object Model

**Read:** [02-page-object-model.md](02-page-object-model.md)
**Code:** `pages/`, then `tests/02_pom/`

```bash
pytest tests/02_pom -v
```

**Exercise 6:** the app has an upload page with a page object already
(`pages/upload_page.py`) but no POM tests. Write `tests/02_pom/test_upload.py` covering: upload
from disk, upload from memory, and the error when you submit with no file.

**Checkpoint:** a designer renames the "Log in" button to "Sign in". How many files do you change?

---

## Day 4 — Fixtures, markers, and data

**Read:** [03-fixtures-and-markers.md](03-fixtures-and-markers.md)

```bash
pytest --fixtures | grep -A3 "authenticated_page\|api_context\|storage_state"
pytest --markers
pytest -m "smoke and not slow" -v
```

**Exercise 7:** add an `admin_page` fixture that is logged in as `admin` rather than `demo`, with
its own storage state, and write one test that uses it.

**Exercise 8:** add a `perf` marker to `pytest.ini`, tag one test with it, and make it run in
neither the smoke nor the regression selection.

**Checkpoint:** you can explain why `configure_timeouts` uses `request.fixturenames` instead of
just taking `page` as an argument.

---

## Day 5 — CI/CD (the big one)

**Read:** [04-ci-cd-explained.md](04-ci-cd-explained.md) with `.github/workflows/ci.yml` open beside it.

**Exercise 9:** in your fork, create a branch, deliberately break one assertion, and open a PR.
Watch the pipeline. Then:

1. Find which shard the failure landed in.
2. Download that shard's artifact and open `report.html`.
3. Open the trace: `playwright show-trace trace.zip`.
4. Read the bot's PR comment and the inline failure annotation.
5. Fix it and watch the comment update rather than duplicate.

**Exercise 10:** change the matrix so WebKit runs only on `main`, not on pull requests. (Hint:
`include` plus an `if:` on the step, or a second job.)

**Checkpoint:** you can explain what `concurrency: cancel-in-progress` saves and what it risks.

---

## Day 6 — Debugging

**Read:** [05-debugging-traces.md](05-debugging-traces.md)

```bash
make debug                          # Playwright Inspector
playwright codegen http://127.0.0.1:5000    # record a script, then improve its locators
make trace
```

**Exercise 11:** run `playwright codegen`, record a login + filter flow, then rewrite the generated
code using page objects and role-based locators. Compare the two. Codegen is a starting point, not
an output.

**Checkpoint:** given only a `trace.zip` from a CI failure, you can say what the page looked like at
the moment of failure.

---

## Day 7 — Flakiness and strategy

**Read:** [06-flaky-tests.md](06-flaky-tests.md)

```bash
pytest -m regression -n auto        # run it three times
pytest -m regression -p no:randomly # and once in file order
```

**Exercise 12:** introduce a flaky test on purpose — make two tests share a hard-coded user ID —
then run with `-n 4` until it fails. Fix it properly (unique data), not with `--reruns`.

**Checkpoint:** you can argue for what belongs in `smoke` versus `regression` on a real product,
and defend the size of your smoke suite.

---

## Where to go next

- Swap the bundled app for your own product; keep `pages/`, `utils/`, `conftest.py` and the workflows
- Add contract tests against your real API and wire them into the `api-tests` job
- Add accessibility checks (`axe-core` via `page.evaluate`) as a new marker and a new CI job
- Add a `staging` environment in GitHub with a required reviewer, and point `manual-run.yml` at it
- Replace `pytest-html` with Allure if your team wants historical trends
