# Getting this onto GitHub

Three routes. Pick one.

---

## Route A — the script (recommended)

Builds a readable, staged commit history rather than one giant "initial commit".

```bash
cd Forkable04EyePythonPlaywrightLearning
chmod +x setup-git.sh

./setup-git.sh                        # local commits only
# or, to create the remote and push in one go:
./setup-git.sh YOUR-GITHUB-USERNAME   # requires the repo to exist on GitHub first
```

Resulting history:

```
docs: add the README, the 7-day learning path and exercise solutions
chore(docker): add Playwright image, compose stack and devcontainer
ci: add dependabot, CODEOWNERS and issue/PR templates
ci: add nightly regression, manual dispatch and Pages publishing
ci: add the main pipeline - lint, api, sharded browser matrix, merged report
ci: add a composite action for python, pip cache and browser cache
test(api): add browserless API tests, UI hybrids and quarantined external tests
test(advanced): add network mocking, storage state, parallel safety and visual
test(pom): rewrite the basics with page objects and data-driven cases
feat(pom): add page objects and a nav-bar component object
test(basics): add lessons 1-5 covering locators, assertions, forms and waiting
feat(framework): add root fixtures, app lifecycle and collection hooks
feat(utils): add env-driven config, logger, data factory and readiness probe
feat(app): add the bundled Flask app under test with a JSON API
chore: add dependencies, pytest config, lint config and Makefile
chore: initialise repo with license and gitignore
```

---

## Route B — GitHub CLI (creates the repo for you)

```bash
gh auth login          # once

cd Forkable04EyePythonPlaywrightLearning
./setup-git.sh         # build the history locally, no remote

gh repo create Forkable04EyePythonPlaywrightLearning \
  --public \
  --source=. \
  --remote=origin \
  --description "Fork-and-learn: Python + Playwright test automation from first script to a production-grade GitHub Actions CI/CD pipeline." \
  --push

# Metadata
gh repo edit --add-topic playwright,python,pytest,test-automation,sdet,qa-automation
gh repo edit --add-topic ci-cd,github-actions,page-object-model,e2e-testing,api-testing,learning-resource
gh repo edit --enable-issues --enable-discussions --enable-wiki=false
gh repo edit --template                       # allow "Use this template"

# Watch the first pipeline
gh run watch
gh run view --log-failed                      # if anything is red
```

---

## Route C — manual, one command at a time

```bash
cd Forkable04EyePythonPlaywrightLearning

git init
git checkout -b main
git add .
git commit -m "feat: python + playwright learning repo with full CI/CD pipeline"

# Create the repo at https://github.com/new (name it Forkable04EyePythonPlaywrightLearning,
# public, and do NOT add a README/gitignore/license -- this repo has them).

git remote add origin https://github.com/suryakulshreshtha/Forkable04EyePythonPlaywrightLearning.git
git push -u origin main
```

---

## One-time setup after the first push

| # | Where | Do this |
| --- | --- | --- |
| 1 | Settings ▸ Pages | Source: **GitHub Actions** — enables the published HTML report |
| 2 | Settings ▸ Branches ▸ Add rule (`main`) | Require PR; require the single check **`CI gate`**; require branch up to date |
| 3 | Settings ▸ General | Tick **Template repository** so people can "Use this template" |
| 4 | `.github/CODEOWNERS` | ✅ already set to `@suryakulshreshtha` |
| 5 | `README.md` | ✅ badges already point at `suryakulshreshtha` |
| 6 | Settings ▸ Secrets and variables ▸ Actions | Optional: add `TEST_PASSWORD` to exercise the secrets path |
| 7 | Actions tab | Run **Manual test run** once to see `workflow_dispatch` inputs in action |

Branch protection via CLI:

```bash
gh api -X PUT "repos/suryakulshreshtha/Forkable04EyePythonPlaywrightLearning/branches/main/protection" \
  -H "Accept: application/vnd.github+json" \
  -f "required_status_checks[strict]=true" \
  -f "required_status_checks[contexts][]=CI gate" \
  -f "required_pull_request_reviews[required_approving_review_count]=1" \
  -F "enforce_admins=true" \
  -F "restrictions=null"
```

> **Require `CI gate`, not the matrix jobs.** Matrix job names include the browser and shard
> number (`UI webkit py3.12 shard 3/4`), so a rule pinned to them breaks the moment you change the
> matrix — and can silently keep passing because the required context is never reported. The
> `ci-gate` job in `ci.yml` aggregates `lint`, `api-tests` and `ui-tests` under one stable name.
> That is the entire reason it exists.

---

## Verify before you push

```bash
make lint          # ruff + black, exactly what the CI lint job runs
make check         # + import every test module
make api           # browserless, ~1s
make test          # full local run

# YAML sanity check on every workflow
python -c "import yaml,glob; [yaml.safe_load(open(f)) for f in glob.glob('.github/**/*.yml', recursive=True)]; print('workflows parse OK')"

git status --porcelain    # should be empty apart from intended changes
```

---

## Useful afterwards

```bash
gh run list --workflow=ci.yml --limit 5
gh run watch
gh run download <run-id> --name report-chromium-py3.12-shard1
playwright show-trace <downloaded>/test-results/<test>/trace.zip

gh workflow run manual-run.yml -f environment=local -f browser=firefox -f markers=smoke
gh workflow run nightly.yml
```
