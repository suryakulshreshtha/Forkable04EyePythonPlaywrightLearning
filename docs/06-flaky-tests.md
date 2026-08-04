# 06 — Flaky tests

> A flaky test is worse than no test. It trains your team to ignore red, and once that habit sets
> in, your real failures get ignored too.

## The five causes, in order of frequency

### 1. Timing

**Symptom:** passes locally, fails on the slower CI runner.
**Cause:** `time.sleep()`, or a plain `assert` where an `expect()` belonged.
**Fix:** delete the sleep, use web-first assertions.

```python
time.sleep(2); assert page.locator("#x").is_visible()   # bad
expect(page.locator("#x")).to_be_visible()              # good
```

### 2. Shared or colliding data

**Symptom:** fails only under `-n auto`, or only on the second run of the day.
**Cause:** two tests using the same user/record, or a hard-coded ID.
**Fix:** generate unique data (`utils/data_factory.py`) and clean up.

Note the detail in `unique_suffix()`: a timestamp alone is not unique, because two calls land in
the same millisecond. It carries a counter as well. This repo had that exact bug during
development and the test suite caught it.

### 3. Order dependency

**Symptom:** passes alone, fails in the suite; or fails when sharded.
**Cause:** test B relies on state test A left behind.
**Fix:** every test creates its own preconditions. Verify with
`pytest --randomly-seed=12345` or by shuffling shards. If two tests genuinely must run in
sequence, they are one test.

### 4. Animations and visual comparison

**Symptom:** screenshot diffs of a few pixels, intermittently.
**Fix:** `reduced_motion: "reduce"` (already set in `browser_context_args`), mask dynamic regions,
allow a `max_diff_pixel_ratio`, and generate baselines on the same OS CI uses.

### 5. Third-party dependencies

**Symptom:** unrelated tests fail when someone else's service has a bad day.
**Fix:** mock it (`page.route`), or quarantine it — which is exactly what `tests/05_external/`
and `continue-on-error: true` are for.

## Skip is not the same as fail

When someone else's server is down, `fail` is the wrong verdict — nothing about your product is
broken, and a suite that cries wolf about infrastructure gets ignored.

```python
try:
    response = request_context.get("/json", timeout=20000)
except PlaywrightError as exc:
    pytest.skip(f"httpbin.org is unreachable from this runner: {exc}")

if response.status >= 500:
    pytest.skip(f"httpbin.org returned {response.status} -- their problem, not ours")
```

Use this only for dependencies genuinely outside your control. Skipping your own flaky test is how
coverage quietly evaporates: track it, and check your skip count in CI the same way you track
failures.

## `filterwarnings = error` — rigorous or a trap?

`pytest.ini` sets warnings to be errors, then ignores `DeprecationWarning`, `ResourceWarning` and
`UserWarning`. That looks like a cop-out; it is the opposite. A bare `error` fails your suite when
the GC collects a socket handle, or when a dependency you do not own adds a deprecation. Both are
red builds with nothing wrong in your code — and the team's fix is always to delete the setting
entirely. Ignore the noise you cannot act on, and the rule survives.

## Retries: a painkiller, not a cure

```ini
--reruns 1 --reruns-delay 2
```

Our PR pipeline retries once; the nightly retries twice. That is deliberate — it keeps a busy
runner's hiccup from blocking a merge. It is **not** permission to leave flakiness in place.

Rules:

- A test that needs retries is a **bug report**, not a passing test.
- Never add retries locally to make a red test green.
- Track the rerun rate. A test that reruns often should be quarantined and fixed.
- Retries hide non-determinism in the *product* too — sometimes the flake is a real race condition
  your users are hitting.

## The quarantine workflow

1. File a **Flaky test** issue (`.github/ISSUE_TEMPLATE/flaky_test.yml`).
2. Remove it from `smoke` so it stops blocking PRs — but leave it running in the nightly.
3. Measure: `pytest path::test --count 50` (with `pytest-repeat`) to get a real failure rate.
4. Fix the cause.
5. Restore its marker.

Steps 2 and 5 are both mandatory. A quarantine with no exit is a deletion with extra steps.

## Detecting flakiness before your users do

```bash
pytest -m regression -n auto        # run three times; any variation is a signal
pytest --count 20 path/to/test.py   # requires pytest-repeat
```

In CI, the nightly is your detector: same code, different day, different result means flaky, not
broken.

## A quality bar you can hold a PR to

- [ ] No `time.sleep`
- [ ] No hard-coded IDs, emails, or usernames
- [ ] Creates its own preconditions; cleans up after itself
- [ ] Passes with `-n 4` and in a random order
- [ ] Locators are role/label/test-id based
- [ ] Fails when the feature is broken (you verified this by breaking it)
