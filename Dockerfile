# The official Playwright image already contains Chromium, Firefox, WebKit and
# every OS-level library they need. Building on anything else means fighting
# missing .so files -- don't.
#
# Keep this tag in sync with the playwright version in requirements.txt.
FROM mcr.microsoft.com/playwright/python:v1.47.0-jammy

WORKDIR /work

# Copy requirements first so Docker caches the (slow) pip layer whenever only
# test code changes. Classic layer-ordering optimisation.
COPY requirements.txt requirements-dev.txt ./
RUN pip install --no-cache-dir -r requirements-dev.txt

COPY . .

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    ENV=ci

# Default: start the app, wait for it, run the suite.
CMD ["bash", "-lc", "python -m app.server & python -m scripts.wait_for_app && pytest -m 'not external'"]
