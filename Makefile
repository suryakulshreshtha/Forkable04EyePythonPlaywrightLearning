# Every target here has a 1:1 twin inside .github/workflows/ci.yml.
# If you can run it locally with make, CI runs the exact same thing.
.PHONY: help install browsers app test smoke regression api parallel headed debug \
        report trace lint audit visual format check clean ci

help:  ## Show this help
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | \
	  awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-12s\033[0m %s\n", $$1, $$2}'

install:  ## Install python deps + dev tooling + browsers
	python -m pip install --upgrade pip
	pip install -r requirements-dev.txt
	python -m playwright install --with-deps

browsers:  ## Install/refresh Playwright browser binaries only
	python -m playwright install --with-deps

app:  ## Run the bundled app under test on http://127.0.0.1:5000
	python -m app.server

test:  ## Run everything except external-internet tests
	pytest -m "not external"

smoke:  ## Critical path only (this is the PR gate)
	pytest -m smoke

regression:  ## Full suite including slow tests
	pytest -m "regression or smoke"

api:  ## API tests only, no browser launched
	pytest -m api

parallel:  ## Run with one worker per CPU core
	pytest -m "not external" -n auto

headed:  ## Watch the browser drive itself
	pytest -m smoke --headed --slowmo 500

debug:  ## Open Playwright Inspector and step through
	PWDEBUG=1 pytest -m smoke --headed -s

visual:  ## Run visual tests locally and (re)generate baselines
	VISUAL=1 pytest -m visual --update-snapshots

report:  ## Open the last HTML report
	python -m webbrowser reports/report.html

trace:  ## Open the trace viewer on the newest trace
	python -m playwright show-trace $$(ls -t reports/test-results/**/trace.zip | head -1)

lint:  ## Ruff + black check (no writes) -- same as the CI lint job
	ruff check .
	black --check .

format:  ## Autofix imports/style
	ruff check --fix .
	black .

audit:  ## Static locator audit -- no browser, ~0.2s. Also runs in CI's lint job.
	python -m scripts.audit_locators

check: lint audit  ## Lint + audit + collect tests without running them
	pytest --collect-only -q

clean:  ## Remove artifacts
	rm -rf reports .pytest_cache .ruff_cache test-results
	find . -type d -name __pycache__ -exec rm -rf {} +

ci: check test  ## What CI effectively does, locally
