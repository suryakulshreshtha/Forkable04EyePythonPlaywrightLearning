# Upload and CI/CD runbook — `suryakulshreshtha`

Repo: `https://github.com/suryakulshreshtha/Forkable04EyePythonPlaywrightLearning`

---

## ⚠️ Read this first — two things that will bite you on macOS/zsh

**1. Never paste a trailing `#` comment with a command.**

zsh does *not* treat `#` as a comment in an interactive shell unless you turn it
on. So this:

```
./setup-git.sh          # local commits only
```

passes `#` to the script as the username and produces the nonsense URL
`https://github.com/#/Forkable04EyePythonPlaywrightLearning.git`, which fails with:

```
fatal: https://github.com/#/....git/info/refs not valid: is this a git repository?
```

Every command in this file is now on its own line with **no trailing comments**.
If you want inline comments to work in your shell, run this once:

```bash
setopt interactive_comments
```

Add it to `~/.zshrc` to make it permanent.

**2. `gh` is optional.** Every step below has a **Without `gh`** path. Install it
only if you want it:

```bash
brew install gh
gh auth login
```

Choose **HTTPS** and let it configure git — that also solves git push
authentication for you.

---

## Step 0 — Local check before you push anything

```bash
cd Forkable04EyePythonPlaywrightLearning
python3 -m venv .venv
source .venv/bin/activate
make install
make check
make test
```

`make check` runs lint + locator audit + import of every test module.
`make test` runs the full suite headless. Both green means CI will be green.

---

## Step 1 — Build the commit history

```bash
chmod +x setup-git.sh
./setup-git.sh
```

The script is **safe to re-run**. If a repo and commits already exist it skips
them rather than failing.

Check the result:

```bash
git log --oneline
git status --porcelain
```

Expect 17 commits and no output from the second command.

Useful variants:

```bash
./setup-git.sh --remote-only suryakulshreshtha
```

```bash
./setup-git.sh --reset suryakulshreshtha
```

The first skips history and only wires the remote. The second deletes `.git`
and rebuilds from scratch.

---

## Step 2 — Create the repo on GitHub

**Do NOT tick "Add a README", ".gitignore" or "license"** — this repo has its
own, and an initial commit on the remote causes a rejected push.

### With `gh`

```bash
gh repo create Forkable04EyePythonPlaywrightLearning --public --source=. --remote=origin --push
```

### Without `gh`

1. Open <https://github.com/new>
2. Name: `Forkable04EyePythonPlaywrightLearning`
3. Visibility: **Public**
4. Leave all three initialisation checkboxes **unticked**
5. Click **Create repository**

Then wire the remote and push:

```bash
./setup-git.sh suryakulshreshtha
```

The script adds the remote (or re-points an existing one), verifies the repo
exists before pushing, and if the push fails it tells you *which* of the three
causes it was.

Doing it by hand instead:

```bash
git remote add origin https://github.com/suryakulshreshtha/Forkable04EyePythonPlaywrightLearning.git
```

If that says `error: remote origin already exists`, re-point it instead:

```bash
git remote set-url origin https://github.com/suryakulshreshtha/Forkable04EyePythonPlaywrightLearning.git
```

Verify, then push:

```bash
git remote -v
git ls-remote origin
git push -u origin main
```

---

## Step 2b — Authentication (only if the push fails)

GitHub removed password auth for HTTPS git in 2021. Your account password will
never work. Pick one:

### (a) GitHub CLI — easiest

```bash
brew install gh
gh auth login
git push -u origin main
```

### (b) Personal access token as the password

Create one at <https://github.com/settings/tokens> → **Tokens (classic)** →
scope **`repo`**. Then:

```bash
git push -u origin main
```

When prompted:

```
Username: suryakulshreshtha
Password: <paste the token>
```

macOS stores it in Keychain, so this is a one-time step.

### (c) SSH

```bash
ssh-keygen -t ed25519 -C "kulshreshtha.surya@engineer.com"
pbcopy < ~/.ssh/id_ed25519.pub
```

Add the key at <https://github.com/settings/keys>, then:

```bash
git remote set-url origin git@github.com:suryakulshreshtha/Forkable04EyePythonPlaywrightLearning.git
git push -u origin main
```

---

## Step 3 — Repo metadata

### With `gh`

```bash
gh repo edit suryakulshreshtha/Forkable04EyePythonPlaywrightLearning --add-topic playwright --add-topic python --add-topic pytest --add-topic test-automation --add-topic sdet
```

```bash
gh repo edit suryakulshreshtha/Forkable04EyePythonPlaywrightLearning --add-topic qa-automation --add-topic ci-cd --add-topic github-actions --add-topic page-object-model --add-topic e2e-testing
```

```bash
gh repo edit suryakulshreshtha/Forkable04EyePythonPlaywrightLearning --add-topic api-testing --add-topic learning-resource
```

```bash
gh repo edit suryakulshreshtha/Forkable04EyePythonPlaywrightLearning --enable-issues --enable-discussions --enable-wiki=false
```

```bash
gh repo edit suryakulshreshtha/Forkable04EyePythonPlaywrightLearning --template
```

### Without `gh` — browser

- **Topics**: repo home page → gear icon next to **About** → add topics → Save
- **Discussions**: Settings → Features → tick **Discussions**
- **Wiki**: Settings → Features → untick **Wikis**
- **Template**: Settings → General → tick **Template repository**

---

## Step 4 — Watch the first pipeline

### With `gh`

```bash
gh run list --limit 5
```

```bash
gh run watch
```

### Without `gh`

Open <https://github.com/suryakulshreshtha/Forkable04EyePythonPlaywrightLearning/actions>

Expected on a push to `main`: `lint` → `api-tests` + `ui-tests` (16 matrix jobs)
+ `external-tests` → `report` → `CI gate`.

If something is red, download the artifact for the failing shard (**Summary**
page, bottom, **Artifacts**), unzip it, and replay the trace:

```bash
playwright show-trace test-results/*/trace.zip
```

With `gh`:

```bash
gh run view --log-failed
```

```bash
gh run download
```

---

## Step 5 — Enable GitHub Pages

Publishes the merged HTML report at
`https://suryakulshreshtha.github.io/Forkable04EyePythonPlaywrightLearning/`

### Browser (works with or without `gh`)

Settings → **Pages** → Build and deployment → Source: **GitHub Actions**

### With `gh`

```bash
gh api -X POST repos/suryakulshreshtha/Forkable04EyePythonPlaywrightLearning/pages -f build_type=workflow
```

---

## Step 6 — Branch protection

Require the single **`CI gate`** check. Do **not** require the matrix jobs —
their names contain the browser and shard number and change whenever you touch
the matrix.

> Do this **after** the first pipeline has finished, so GitHub already knows the
> check name `CI gate` exists.

### Browser

Settings → **Branches** → **Add branch protection rule**

- Branch name pattern: `main`
- ✅ Require a pull request before merging
- ✅ Require status checks to pass → search for and select **`CI gate`**
- ✅ Require branches to be up to date before merging
- ✅ Do not allow bypassing the above settings

### With `gh`

```bash
gh api -X PUT repos/suryakulshreshtha/Forkable04EyePythonPlaywrightLearning/branches/main/protection -H "Accept: application/vnd.github+json" -f "required_status_checks[strict]=true" -f "required_status_checks[contexts][]=CI gate" -f "required_pull_request_reviews[required_approving_review_count]=1" -F "enforce_admins=true" -F "restrictions=null"
```

Verify:

```bash
gh api repos/suryakulshreshtha/Forkable04EyePythonPlaywrightLearning/branches/main/protection --jq '.required_status_checks.contexts'
```

---

## Step 7 — Optional secrets and environments

### With `gh`

```bash
gh secret set TEST_PASSWORD --body "Password123"
```

```bash
gh variable set BASE_URL --body "http://127.0.0.1:5000"
```

### Without `gh`

Settings → **Secrets and variables** → **Actions** → **New repository secret**
/ **New repository variable**.

For a gated staging run: Settings → **Environments** → **New environment** →
`staging` → tick **Required reviewers**.

---

## Step 8 — Prove the pipeline actually blocks a bad merge

```bash
git checkout -b demo/break-a-test
```

```bash
sed -i.bak 's/Welcome back, demo./Welcome back, WRONG./' tests/01_basics/test_01_first_test.py
```

```bash
git commit -am "test: deliberately break an assertion to demo the pipeline"
```

```bash
git push -u origin demo/break-a-test
```

Open the PR — with `gh`:

```bash
gh pr create --fill
```

Without `gh`: GitHub shows a **Compare & pull request** banner on the repo page.

Then watch for, in order:

1. `lint` passes — it is valid Python
2. one `ui-tests` shard goes red
3. the bot posts a pass/fail table as a PR comment
4. the failure appears as an inline annotation on **Files changed**
5. `CI gate` fails and the merge button is blocked

Fix it and confirm the comment **updates** rather than duplicating:

```bash
mv tests/01_basics/test_01_first_test.py.bak tests/01_basics/test_01_first_test.py
```

```bash
git commit -am "fix: restore the assertion"
```

```bash
git push
```

Clean up:

```bash
git checkout main
```

```bash
git branch -D demo/break-a-test
```

```bash
git push origin --delete demo/break-a-test
```

---

## Everyday commands

### Local test lanes (mirrors of the CI jobs)

```bash
make smoke
make test
make regression
make api
make parallel
make headed
make debug
make audit
make trace
make visual
```

```bash
pytest --splits 4 --group 2
```

```bash
pytest --browser webkit -m smoke
```

```bash
pytest --base-url https://staging.example.com -m smoke
```

### Pipeline control, with `gh`

```bash
gh workflow list
```

```bash
gh workflow run manual-run.yml -f environment=local -f browser=firefox -f markers=smoke -f workers=2
```

```bash
gh workflow run nightly.yml
```

```bash
gh run list --workflow=ci.yml --limit 10
```

```bash
gh run rerun <run-id> --failed
```

Without `gh`: the **Actions** tab → pick a workflow → **Run workflow** button
gives you the same typed inputs, and each run page has **Re-run failed jobs**.

---

## Visual baselines — one-time, when you want that gate real

The repo intentionally ships **no** screenshot baselines: they must be generated
on the CI runner's OS, not your laptop.

```bash
gh workflow run nightly.yml
```

```bash
gh run download <run-id> --name visual-baselines-and-diffs
```

Inspect every PNG, then:

```bash
cp -r visual-baselines-and-diffs/tests/ tests/
```

```bash
git add tests/**/__snapshots__
```

```bash
git commit -m "test(visual): add screenshot baselines generated on ubuntu-latest"
```

```bash
git push
```

Then set `continue-on-error: false` on the `visual-suite` job in
`.github/workflows/nightly.yml` to turn it into a real gate.

To regenerate locally instead (fonts will differ from CI):

```bash
make visual
```

---

## Troubleshooting

| Error | Cause | Fix |
| --- | --- | --- |
| `https://github.com/#/....git/info/refs not valid` | zsh passed a pasted `#` comment as the username | Re-run the command with no trailing comment. `git remote set-url origin https://github.com/suryakulshreshtha/Forkable04EyePythonPlaywrightLearning.git` |
| `error: remote origin already exists` | `git remote add` run twice | Use `git remote set-url origin <url>` |
| `This directory is already a git repo` | Old version of `setup-git.sh` | Fixed — the script is now idempotent. `./setup-git.sh --remote-only suryakulshreshtha` |
| `zsh: command not found: gh` | GitHub CLI not installed | `brew install gh && gh auth login`, or use the **Without `gh`** path in every step |
| `could not read Username for 'https://github.com'` | No credential helper / not authenticated | Step 2b |
| `Authentication failed` / `403` | Using your account password | Step 2b — password auth was removed in 2021; use a token, `gh`, or SSH |
| `Repository not found` | Repo not created yet, or wrong username | Create it at <https://github.com/new>, then `./setup-git.sh --remote-only suryakulshreshtha` |
| `Updates were rejected` / `non-fast-forward` | Repo was created **with** a README | `git push --force-with-lease origin main` (discards the remote README) or `git pull --rebase origin main` first |
| `src refspec main does not match any` | No commits yet, or branch is `master` | `./setup-git.sh` then `git branch -M main` |
| `CI gate` not offered as a required check | Protection set before the first run | Let one pipeline finish, then redo Step 6 |
| Pages deploy 403 | Pages not enabled | Step 5 |
| Every UI test fails `ERR_CONNECTION_REFUSED` | App not started in the job | Check the "Wait for app to be healthy" step in the job log |
