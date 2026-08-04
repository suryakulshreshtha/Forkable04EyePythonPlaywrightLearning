# Contributing

This is a teaching repo. Contributions that make a concept *clearer* are as welcome as new tests.

## Setup

```bash
make install
pre-commit install
```

## Before you open a PR

```bash
make lint       # ruff + black, exactly what CI runs
make audit      # locator audit -- 0.2s, no browser
make check      # lint + audit + import every test module
make test       # everything except external
make parallel   # prove it survives -n auto
```

## Test quality bar

1. **No `time.sleep()`.** Use auto-waiting or `expect()`.
2. **No hard-coded URLs or credentials.** Everything through `utils/config.py`.
3. **No inter-test dependencies.** Each test creates its own preconditions.
4. **Locators**: role → label → test-id → CSS. XPath needs a comment justifying it.
5. **Page objects never assert.** They expose actions and state.
6. **Markers**: `smoke` is the PR gate — add to it only if the app is unusable when it fails.
7. **Prove it works.** Break the feature, watch the test fail, fix it, watch it pass.

## Teaching style

This repo's comments explain *why*, not *what*. `# click the button` is noise; `# expect_download
must wrap the click, not follow it` is the reason someone forked this. When you add a test, add
the reasoning.

## Commit messages

Conventional commits: `test:`, `feat:`, `fix:`, `ci:`, `docs:`, `chore:`, `refactor:`.

```
test(dashboard): cover combined role and name filtering
ci: shard the UI matrix four ways to halve wall-clock time
```

## Reporting a flaky test

Use the **Flaky test** issue template. Include the node ID, the observed failure rate, and links
to failing runs. Do not "fix" it by adding `--reruns`.
