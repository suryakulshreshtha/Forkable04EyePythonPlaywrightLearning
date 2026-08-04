"""Tiny logging helper.

In CI, print()s vanish into a 5000-line log. A consistent prefix plus GitHub
Actions log grouping makes failures skimmable.
"""

from __future__ import annotations

import logging
import os
import sys
from contextlib import contextmanager

_FORMAT = "%(asctime)s | %(levelname)-7s | %(name)s | %(message)s"


def get_logger(name: str = "e2e") -> logging.Logger:
    logger = logging.getLogger(name)
    if not logger.handlers:
        handler = logging.StreamHandler(sys.stdout)
        handler.setFormatter(logging.Formatter(_FORMAT, datefmt="%H:%M:%S"))
        logger.addHandler(handler)
        logger.setLevel(os.environ.get("LOG_LEVEL", "INFO").upper())
        logger.propagate = False
    return logger


@contextmanager
def log_group(title: str):
    """Collapsible section in the GitHub Actions log; plain text elsewhere."""
    in_actions = os.environ.get("GITHUB_ACTIONS") == "true"
    print(f"::group::{title}" if in_actions else f"--- {title} ---")
    try:
        yield
    finally:
        print("::endgroup::" if in_actions else "--- end ---")
