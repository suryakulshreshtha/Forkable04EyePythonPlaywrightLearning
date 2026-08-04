"""Block until the app under test answers /health, or exit non-zero.

Why this exists
---------------
In CI the Flask app is started in the background. If pytest starts before the
socket is listening, every test fails with ERR_CONNECTION_REFUSED and you waste
a pipeline run chasing a phantom bug. A readiness probe is the fix -- this is
the same pattern as `wait-on`, `dockerize -wait`, or a k8s readinessProbe.
"""

from __future__ import annotations

import sys
import time
import urllib.error
import urllib.request

URL = sys.argv[1] if len(sys.argv) > 1 else "http://127.0.0.1:5000/health"
TIMEOUT_SECONDS = int(sys.argv[2]) if len(sys.argv) > 2 else 60


def main() -> int:
    deadline = time.time() + TIMEOUT_SECONDS
    attempt = 0
    while time.time() < deadline:
        attempt += 1
        try:
            with urllib.request.urlopen(URL, timeout=2) as response:  # noqa: S310
                if response.status == 200:
                    print(f"App is up after {attempt} attempt(s): {URL}")
                    return 0
        except (urllib.error.URLError, OSError) as exc:
            print(f"  attempt {attempt}: not ready yet ({exc.__class__.__name__})")
        time.sleep(1)

    print(f"ERROR: {URL} did not become healthy within {TIMEOUT_SECONDS}s")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
