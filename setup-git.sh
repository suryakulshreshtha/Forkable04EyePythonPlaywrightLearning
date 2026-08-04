#!/usr/bin/env bash
# =============================================================================
# setup-git.sh -- initialise the repo, build a readable commit history, and
#                 (optionally) wire up the GitHub remote and push.
#
# SAFE TO RE-RUN. Every stage detects what has already been done and skips it,
# so running this twice does nothing harmful. That matters: the most common way
# a setup script hurts you is by being all-or-nothing and leaving you halfway.
#
# Usage:
#   ./setup-git.sh                       # commits only, no remote
#   ./setup-git.sh suryakulshreshtha     # commits + remote + push
#   ./setup-git.sh --remote-only <user>  # skip history, just wire the remote
#   ./setup-git.sh --reset <user>        # DELETE .git and rebuild from scratch
# =============================================================================
set -euo pipefail

REPO_NAME="Forkable04EyePythonPlaywrightLearning"
DEFAULT_USER="suryakulshreshtha"

REMOTE_ONLY=false
RESET=false
GH_USER=""

# ---------------------------------------------------------------------------
# Argument parsing, with a guard for a trap that bites almost everyone on zsh.
#
# zsh does NOT strip `#` comments in an interactive shell unless
# `interactive_comments` is set. So pasting:
#     ./setup-git.sh          # local commits only
# passes "#" as $1, and a naive script happily builds
#     https://github.com/#/Forkable04EyePythonPlaywrightLearning.git
# which fails with a baffling "not valid: is this a git repository?".
# Validate the username instead of trusting it.
# ---------------------------------------------------------------------------
valid_username () {
  # GitHub: alphanumerics and single hyphens, cannot start/end with a hyphen,
  # 39 chars max.
  [[ "$1" =~ ^[A-Za-z0-9]([A-Za-z0-9-]{0,37}[A-Za-z0-9])?$ ]]
}

while [ $# -gt 0 ]; do
  case "$1" in
    --remote-only) REMOTE_ONLY=true; shift ;;
    --reset)       RESET=true; shift ;;
    -h|--help)
      sed -n '2,26p' "$0"; exit 0 ;;
    -*)
      echo "Unknown option: $1"; exit 2 ;;
    *)
      if [ -n "$GH_USER" ]; then
        # A second positional argument almost always means a pasted comment.
        cat <<MSG

ERROR: unexpected extra argument: '$1'

If you pasted a line like:

    ./setup-git.sh $GH_USER          # commits, adds the remote, pushes

...then zsh passed the '#' and every word after it to this script as
arguments, because zsh does not treat '#' as a comment in interactive shells.

Run the command on its own, with nothing after it:

    ./setup-git.sh $GH_USER

Or enable comment handling once for this shell:

    setopt interactive_comments

MSG
        exit 2
      fi
      if ! valid_username "$1"; then
        cat <<MSG

ERROR: '$1' is not a valid GitHub username.

This is nearly always the zsh comment trap: pasting

    ./setup-git.sh          # local commits only

passes '#' as the username, and the script would then build the nonsense URL
    https://github.com/#/${REPO_NAME}.git

Run it without the trailing comment:

    ./setup-git.sh                      # <- paste ONLY the command part
    ./setup-git.sh ${DEFAULT_USER}

MSG
        exit 2
      fi
      GH_USER="$1"; shift ;;
  esac
done

command -v git >/dev/null || { echo "ERROR: git is not installed."; exit 1; }

say()  { printf '\n\033[1m==> %s\033[0m\n' "$1"; }
ok()   { printf '    \033[32mok\033[0m   %s\n' "$1"; }
skip() { printf '    \033[33mskip\033[0m %s\n' "$1"; }
warn() { printf '    \033[33mwarn\033[0m %s\n' "$1"; }

# ---------------------------------------------------------------------------
# 0. Optional hard reset
# ---------------------------------------------------------------------------
if [ "$RESET" = true ] && [ -d .git ]; then
  say "--reset given: deleting the existing .git directory"
  rm -rf .git
  ok "history removed, starting fresh"
fi

# ---------------------------------------------------------------------------
# 1. Repository
# ---------------------------------------------------------------------------
say "Repository"
if [ -d .git ]; then
  skip "already a git repo (re-running is safe)"
else
  git init -q
  ok "git init"
fi

# git init respects init.defaultBranch, which may be 'master'. Normalise.
CURRENT_BRANCH="$(git symbolic-ref --quiet --short HEAD 2>/dev/null || echo main)"
if [ "$CURRENT_BRANCH" != "main" ]; then
  git branch -M main 2>/dev/null || git checkout -q -b main
  ok "branch normalised to 'main' (was '$CURRENT_BRANCH')"
else
  ok "on branch main"
fi

# A commit needs an identity. Fail with a useful message, not git's.
if ! git config user.email >/dev/null && ! git config --global user.email >/dev/null; then
  cat <<'MSG'

ERROR: git has no identity configured, so it cannot create commits.
Set one first:

    git config --global user.name  "Surya Kulshreshtha"
    git config --global user.email "you@example.com"

MSG
  exit 1
fi

# ---------------------------------------------------------------------------
# 2. Commit history
# ---------------------------------------------------------------------------
HAS_COMMITS=false
git rev-parse --verify HEAD >/dev/null 2>&1 && HAS_COMMITS=true

if [ "$REMOTE_ONLY" = true ]; then
  say "Commit history"
  skip "--remote-only given"
elif [ "$HAS_COMMITS" = true ]; then
  say "Commit history"
  skip "$(git rev-list --count HEAD) commit(s) already exist -- not rebuilding"
  if [ -n "$(git status --porcelain)" ]; then
    git add -A
    git commit -q -m "chore: commit outstanding changes"
    ok "committed outstanding working-tree changes"
  fi
else
  say "Building commit history"

  # These are all in .gitignore anyway; belt and braces.
  rm -rf reports .pytest_cache .ruff_cache .auth test-results 2>/dev/null || true
  find . -type d -name __pycache__ -prune -exec rm -rf {} + 2>/dev/null || true

  # NOTE: stages nothing itself. Each call below adds its own paths first, so
  # the history reads in the order the docs teach. A "git add -A" in here would
  # stage the whole repo on the first call and leave every later commit empty.
  commit () { git commit -q -m "$1"; printf '    %s\n' "$1"; }

  git add .gitignore .gitattributes LICENSE
  commit "chore: initialise repo with license and gitignore"

  git add requirements.txt requirements-dev.txt pytest.ini pyproject.toml Makefile \
          .pre-commit-config.yaml .env.example
  commit "chore: add dependencies, pytest config, lint config and Makefile"

  git add app/ test-data/
  commit "feat(app): add the bundled Flask app under test with a JSON API"

  git add utils/ scripts/
  commit "feat(utils): add config, logger, data factory, readiness probe and locator audit"

  git add conftest.py tests/conftest.py tests/__init__.py
  commit "feat(framework): add root fixtures, app lifecycle and collection hooks"

  git add tests/01_basics/
  commit "test(basics): add lessons 1-5 covering locators, assertions, forms and waiting"

  git add pages/
  commit "feat(pom): add page objects and a nav-bar component object"

  git add tests/02_pom/
  commit "test(pom): rewrite the basics with page objects and data-driven cases"

  git add tests/03_advanced/
  commit "test(advanced): add network mocking, storage state, parallel safety and visual"

  git add tests/04_api/ tests/05_external/
  commit "test(api): add browserless API tests, UI hybrids and quarantined external tests"

  git add .github/actions/
  commit "ci: add a composite action for python, pip cache and browser cache"

  git add .github/workflows/ci.yml
  commit "ci: add the main pipeline - lint, api, sharded browser matrix, gate and report"

  git add .github/workflows/nightly.yml .github/workflows/manual-run.yml \
          .github/workflows/publish-report.yml
  commit "ci: add nightly regression, manual dispatch and Pages publishing"

  git add .github/dependabot.yml .github/CODEOWNERS .github/ISSUE_TEMPLATE \
          .github/pull_request_template.md
  commit "ci: add dependabot, CODEOWNERS and issue/PR templates"

  git add Dockerfile docker-compose.yml .devcontainer/
  commit "chore(docker): add Playwright image, compose stack and devcontainer"

  git add docs/ README.md CONTRIBUTING.md UPLOAD_STEPS.md
  commit "docs: add the README, the 7-day learning path, solutions and upload runbook"

  git add -A
  if ! git diff --cached --quiet; then
    commit "chore: add git setup script and command reference"
  fi

  ok "$(git rev-list --count HEAD) commits built"
fi

# ---------------------------------------------------------------------------
# 3. Remote
# ---------------------------------------------------------------------------
if [ -z "$GH_USER" ]; then
  say "Remote"
  skip "no username given"
  cat <<MSG

Done locally. To publish:

    ./setup-git.sh $DEFAULT_USER          # re-run, this time with the username
  or manually:
    git remote add origin https://github.com/$DEFAULT_USER/${REPO_NAME}.git
    git push -u origin main

MSG
  git --no-pager log --oneline
  exit 0
fi

REMOTE_URL="https://github.com/${GH_USER}/${REPO_NAME}.git"

say "Remote"
if git remote get-url origin >/dev/null 2>&1; then
  EXISTING="$(git remote get-url origin)"
  if [ "$EXISTING" = "$REMOTE_URL" ]; then
    skip "origin already points at $REMOTE_URL"
  else
    git remote set-url origin "$REMOTE_URL"
    ok "origin re-pointed: $EXISTING -> $REMOTE_URL"
  fi
else
  git remote add origin "$REMOTE_URL"
  ok "origin added: $REMOTE_URL"
fi

# ---------------------------------------------------------------------------
# 4. Does the remote actually exist? Check BEFORE pushing.
# ---------------------------------------------------------------------------
say "Checking the remote exists"
if git ls-remote "$REMOTE_URL" >/dev/null 2>&1; then
  ok "remote repository is reachable"
else
  cat <<MSG

    The remote does not exist yet (or you are not authenticated).

    Create it, then re-run this script:

      With the GitHub CLI:
        gh auth login
        gh repo create ${REPO_NAME} --public --source=. --remote=origin --push

      Or in a browser:
        https://github.com/new
        Name: ${REPO_NAME}   Visibility: Public
        Do NOT tick "Add a README", ".gitignore" or "license" -- this repo has
        its own, and an initial commit on the remote causes the rejected-push
        error below.

      Then:
        ./setup-git.sh --remote-only ${GH_USER}

MSG
  exit 1
fi

# ---------------------------------------------------------------------------
# 5. Push
# ---------------------------------------------------------------------------
say "Pushing to origin/main"
PUSH_LOG="$(mktemp)"
if git push -u origin main 2>&1 | tee "$PUSH_LOG"; then
  ok "pushed"
  rm -f "$PUSH_LOG"
else
  # Diagnose the ACTUAL failure instead of guessing. The three causes look
  # nothing alike to git and identical to a beginner.
  if grep -qiE "could not read Username|Authentication failed|Invalid username or password|Permission denied|403" "$PUSH_LOG"; then
    cat <<MSG

    AUTHENTICATION failed. GitHub removed password auth for git over HTTPS in
    2021, so your account password will never work here. Pick one:

    (a) GitHub CLI -- easiest, also unlocks every gh command in UPLOAD_STEPS.md
        brew install gh
        gh auth login          (choose HTTPS, and let it configure git)
        git push -u origin main

    (b) Personal access token used as the PASSWORD
        Create at https://github.com/settings/tokens
          - "Tokens (classic)", scope: repo        (or a fine-grained token
            with Contents: read+write on this repo)
        Then:
          git push -u origin main
          Username: ${GH_USER}
          Password: <paste the token, NOT your account password>
        macOS will store it in Keychain, so you do this once.

    (c) SSH instead of HTTPS
        ssh-keygen -t ed25519 -C "you@example.com"
        pbcopy < ~/.ssh/id_ed25519.pub        then add it at
        https://github.com/settings/keys
        git remote set-url origin git@github.com:${GH_USER}/${REPO_NAME}.git
        git push -u origin main

MSG
  elif grep -qiE "Repository not found|does not appear to be a git repository" "$PUSH_LOG"; then
    cat <<MSG

    The remote repository does not exist, or your account cannot see it.

    Create it at https://github.com/new
      Name: ${REPO_NAME}
      Visibility: Public
      Do NOT tick README / .gitignore / license.
    Then re-run:
      ./setup-git.sh --remote-only ${GH_USER}

MSG
  elif grep -qiE "rejected|non-fast-forward|fetch first|behind" "$PUSH_LOG"; then
    cat <<MSG

    Push REJECTED: the remote has commits yours does not. This happens when the
    GitHub repo was created WITH a README.

    Look at what is there:
        git fetch origin
        git --no-pager log --oneline origin/main

    If it is only GitHub's auto-generated README and you do not want it:
        git push --force-with-lease origin main

    If you want to keep it:
        git pull --rebase origin main
        git push -u origin main

    (--force-with-lease, never plain --force: it refuses if someone else pushed
    in the meantime, which --force would silently destroy.)

MSG
  else
    cat <<MSG

    Push failed. Full output above; the last few lines are the useful part.
    Re-run just the push once you have addressed it:
        git push -u origin main

MSG
  fi
  rm -f "$PUSH_LOG"
  exit 1
fi

# ---------------------------------------------------------------------------
# 6. What is left to do by hand
# ---------------------------------------------------------------------------
cat <<MSG

$(git --no-pager log --oneline | head -20)

Pushed to https://github.com/${GH_USER}/${REPO_NAME}

Remaining one-time setup (see UPLOAD_STEPS.md steps 3-7):
  1. Settings > Pages     -> Source: GitHub Actions
  2. Run the pipeline once, THEN protect main requiring the "CI gate" check
  3. Settings > General   -> tick "Template repository"
  4. CODEOWNERS and README badges already say ${GH_USER}

Watch the first run:
  gh run watch

MSG
