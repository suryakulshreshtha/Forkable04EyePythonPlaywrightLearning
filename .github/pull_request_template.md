## What does this change?

<!-- One or two sentences. Link the issue: Closes #123 -->

## Type of change

- [ ] New test coverage
- [ ] Fix for a failing/flaky test
- [ ] Framework or fixture change
- [ ] CI/CD pipeline change
- [ ] Documentation

## Test-quality checklist

- [ ] The test fails when the feature is broken (I checked by breaking it)
- [ ] No `time.sleep()` — auto-waiting or `expect()` only
- [ ] No hard-coded URLs, usernames or passwords — everything via `utils/config.py`
- [ ] No dependency on another test's data or ordering
- [ ] Passes with `-n 4` (parallel) as well as serially
- [ ] Locators use role/label/test-id, not brittle CSS or XPath
- [ ] Correct marker applied (`smoke` for critical path only)
- [ ] `make lint` is clean

## CI

- [ ] All required checks are green
- [ ] If I changed a workflow, I explained why in the description

## Screenshots / trace

<!-- For UI changes or a fixed failure, attach the trace or a screenshot. -->
