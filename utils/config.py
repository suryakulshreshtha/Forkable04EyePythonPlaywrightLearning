"""Environment-driven configuration.

Rule of thumb for CI: a test must never contain a hard-coded URL, username or
password. Everything comes from here, and here reads from environment variables
with local-friendly defaults. That is what lets the SAME suite run against
local, ci, and staging with only env vars changing.
"""

from __future__ import annotations

import os
from dataclasses import dataclass, field

try:  # optional: .env support for local runs
    from dotenv import load_dotenv

    load_dotenv()
except ImportError:  # pragma: no cover - dotenv is optional
    pass


def _bool(name: str, default: bool) -> bool:
    return os.environ.get(name, str(default)).strip().lower() in {"1", "true", "yes", "on"}


@dataclass(frozen=True)
class Settings:
    env: str = field(default_factory=lambda: os.environ.get("ENV", "local"))
    base_url: str = field(
        default_factory=lambda: os.environ.get("BASE_URL", "http://127.0.0.1:5000").rstrip("/")
    )
    username: str = field(default_factory=lambda: os.environ.get("TEST_USER", "demo"))
    password: str = field(default_factory=lambda: os.environ.get("TEST_PASSWORD", "Password123"))
    headless: bool = field(default_factory=lambda: _bool("HEADLESS", True))
    slow_mo: int = field(default_factory=lambda: int(os.environ.get("SLOW_MO", "0")))
    default_timeout_ms: int = field(
        default_factory=lambda: int(os.environ.get("DEFAULT_TIMEOUT_MS", "10000"))
    )

    @property
    def is_ci(self) -> bool:
        # GitHub Actions always sets CI=true. Handy for "retry only in CI".
        return os.environ.get("CI", "").lower() == "true" or self.env == "ci"

    def url(self, path: str = "/") -> str:
        return f"{self.base_url}/{path.lstrip('/')}"

    def masked(self) -> dict:
        """Safe to print in logs -- never dump raw secrets into CI output."""
        return {
            "env": self.env,
            "base_url": self.base_url,
            "username": self.username,
            "password": "***" if self.password else "(empty)",
            "headless": self.headless,
            "is_ci": self.is_ci,
        }


settings = Settings()
