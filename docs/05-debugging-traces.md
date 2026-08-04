# 05 — Debugging

## Before you debug: is it the locator?

```bash
make audit      # 0.2s, no browser
```

`scripts/audit_locators.py` checks every locator literal in `pages/` and `tests/` against the
rendered app, and flags any `get_by_label` that would trip strict mode. If a test broke right
after someone touched the templates, this tells you which locator died before you launch anything.

## The escalation ladder

1. Read the error. Playwright's messages are unusually good — they tell you what the locator
   resolved to and what it waited for.
2. `--headed --slowmo 500` — watch it.
3. `PWDEBUG=1` — Playwright Inspector: step through, live-edit locators.
4. Open the trace — especially for CI failures you cannot reproduce.

## Headed and slow motion

```bash
pytest tests/02_pom/test_login.py --headed --slowmo 800
make headed
```

## Playwright Inspector

```bash
PWDEBUG=1 pytest tests/02_pom/test_login.py -k valid --headed -s
make debug
```

The Inspector pauses before each action, shows the resolved locator, and has a **Pick locator**
button that generates a locator by clicking the page. Use it to check whether your locator is
ambiguous *before* strict mode tells you it is.

`page.pause()` in code does the same thing at an exact point.

## Traces — the important one

A trace records the whole run: a DOM snapshot before and after every action, network, console,
screenshots, and timings. It is how you debug a CI failure without reproducing it.

We capture `retain-on-failure` (see `pytest.ini`), so passing runs cost nothing.

```bash
playwright show-trace reports/test-results/<test>/trace.zip
make trace                # opens the newest one
```

From CI: download the `report-*` artifact for the failing shard, unzip, and point
`show-trace` at the `trace.zip` inside.

What to do in the viewer:

- Scrub the timeline to the red step
- Toggle **Before / Action / After** snapshots — the DOM is live and inspectable
- Check **Network** for a 500 or a request that never fired
- Check **Console** for a JS error that broke rendering
- Compare the "expected" locator against the actual DOM at that instant

## Codegen

```bash
playwright codegen http://127.0.0.1:5000
```

Records your clicks into Python. Treat the output as a **draft**: it often picks positional or
text locators you would not choose, and it never produces page objects. Rewrite it.

## Other tools

```bash
pytest -x                 # stop at the first failure
pytest --lf               # rerun last failures only
pytest --sw               # stepwise: stop, fix, continue from there
pytest -vv --tb=long      # full tracebacks
pytest -s                 # let print() through
pytest --collect-only     # what would run, without running it
pytest --setup-plan       # the fixture graph for those tests
```

Video (`--video on`) and screenshots (`--screenshot on`) are useful for a demo or a bug report,
but a trace beats both for actual debugging.

## Debugging a CI-only failure — the checklist

1. Did it fail on all browsers or one? One browser usually means a real engine difference.
2. Did it fail on all shards or one? One shard hints at test-order or data collision.
3. Download the trace. Look at the DOM snapshot at failure.
4. Reproduce the CI conditions locally: `HEADLESS=true pytest -n 2 --browser webkit`.
5. Still passing locally? Suspect timing (CI runners are slower), timezone/locale, or shared state.
