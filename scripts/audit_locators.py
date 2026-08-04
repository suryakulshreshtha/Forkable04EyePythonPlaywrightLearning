"""Static locator audit -- catch broken locators in seconds, without a browser.

What it does
------------
1. Walks `pages/` and `tests/` with the `ast` module and harvests every literal
   passed to `get_by_test_id`, `get_by_label`, `get_by_role`, `get_by_placeholder`.
2. Renders every page of the bundled app with Flask's test client.
3. Checks that each locator literal actually resolves, and that no
   `get_by_label` is ambiguous (which strict mode would reject at runtime).

Why bother when the tests already prove it?
-------------------------------------------
Because this takes ~0.2s and needs no browser, so it can run in the `lint` job
before the eight-minute matrix starts. A renamed `data-testid` is caught in the
first 40 seconds of CI instead of the ninth minute. It is the locator equivalent
of `pytest --collect-only`.

Limitations, stated honestly: it is a static approximation. It cannot evaluate
computed locators, it does not model the full ARIA accessible-name algorithm,
and it skips `tests/05_external/` because those target sites we do not control.

Usage:
    python -m scripts.audit_locators          # exits non-zero on a problem
"""

from __future__ import annotations

import ast
import io
import os
import pathlib
import sys
from html.parser import HTMLParser

from app.server import create_app

SEARCH_ROOTS = ("pages", "tests")
SKIP_DIRS = {"05_external"}  # external sites are not ours to validate
VOID_TAGS = {"input", "br", "img", "meta", "link", "hr", "source", "area", "col"}

TRACKED = ("get_by_test_id", "get_by_label", "get_by_role", "get_by_placeholder")


# ---------------------------------------------------------------------------
# 1. Harvest locator literals from the source
# ---------------------------------------------------------------------------
def harvest() -> dict[str, list[tuple]]:
    found: dict[str, list[tuple]] = {name: [] for name in TRACKED}

    for root in SEARCH_ROOTS:
        for path in pathlib.Path(root).rglob("*.py"):
            if any(part in SKIP_DIRS for part in path.parts):
                continue
            tree = ast.parse(path.read_text(encoding="utf-8"))
            for node in ast.walk(tree):
                if not (isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute)):
                    continue
                fn = node.func.attr
                if fn not in found:
                    continue
                args = [
                    a.value
                    for a in node.args
                    if isinstance(a, ast.Constant) and isinstance(a.value, str)
                ]
                kwargs = {
                    k.arg: k.value.value
                    for k in node.keywords
                    if isinstance(k.value, ast.Constant) and isinstance(k.value.value, str)
                }
                if not args:
                    continue  # computed locator, e.g. built from a variable
                if fn == "get_by_role":
                    found[fn].append((args[0], kwargs.get("name"), str(path)))
                else:
                    found[fn].append((args[0], str(path)))
    return found


# ---------------------------------------------------------------------------
# 2. Render every page and parse it
# ---------------------------------------------------------------------------
class Doc(HTMLParser):
    """Minimal accessibility-ish index of a rendered page."""

    def __init__(self) -> None:
        super().__init__()
        self.labels: list[tuple[str, str | None]] = []  # (text, for=)
        self.aria: list[tuple[str, str]] = []  # (aria-label, tag)
        self.buttons: list[str] = []
        self.links: list[str] = []
        self.headings: list[str] = []
        self.placeholders: set[str] = set()
        self._stack: list[tuple[str, dict, list[str]]] = []

    def handle_starttag(self, tag, attrs):
        attributes = dict(attrs)
        if attributes.get("aria-label"):
            self.aria.append((attributes["aria-label"], tag))
        if attributes.get("placeholder"):
            self.placeholders.add(attributes["placeholder"])
        # Void elements never close, so pushing them would swallow the text that
        # follows -- which is exactly how a wrapping <label><input> Text</label>
        # gets mis-parsed.
        if tag not in VOID_TAGS:
            self._stack.append((tag, attributes, []))

    def handle_data(self, data):
        if self._stack:
            self._stack[-1][2].append(data)

    def handle_endtag(self, tag):
        while self._stack:
            name, attributes, chunks = self._stack.pop()
            text = " ".join("".join(chunks).split())
            if name == "label":
                self.labels.append((text, attributes.get("for")))
            elif name == "button":
                self.buttons.append(text)
            elif name == "a":
                self.links.append(text)
            elif name in {"h1", "h2", "h3", "h4"}:
                self.headings.append(text)
            if name == tag:
                break


def render_pages() -> tuple[dict[str, Doc], str]:
    app = create_app()
    client = app.test_client()

    sources: dict[str, str] = {}
    sources["login"] = client.get("/").get_data(as_text=True)
    sources["login-error"] = client.post(
        "/login", data={"username": "nope", "password": "nope"}
    ).get_data(as_text=True)

    client.post("/login", data={"username": "demo", "password": "Password123"})
    sources["dashboard"] = client.get("/dashboard").get_data(as_text=True)
    sources["upload"] = client.get("/upload").get_data(as_text=True)
    sources["upload-done"] = client.post(
        "/upload",
        data={"document": (io.BytesIO(b"line one\nline two\n"), "sample-upload.txt")},
        content_type="multipart/form-data",
    ).get_data(as_text=True)
    sources["flaky"] = client.get("/flaky").get_data(as_text=True)

    docs = {}
    for name, html_source in sources.items():
        doc = Doc()
        doc.feed(html_source)
        docs[name] = doc

    # Rows are created by JavaScript, so also search the raw template text.
    templates = "\n".join(
        p.read_text(encoding="utf-8") for p in pathlib.Path("app/templates").glob("*.html")
    )
    return docs, "\n".join(sources.values()) + "\n" + templates


# ---------------------------------------------------------------------------
# 3. Checks
# ---------------------------------------------------------------------------
def label_hits(doc: Doc, text: str) -> int:
    """How many distinct controls this label text would resolve to on one page."""
    needle = text.casefold()
    explicit = {f for t, f in doc.labels if needle in t.casefold() and f}
    wrapping = sum(1 for t, f in doc.labels if needle in t.casefold() and not f)
    aria = {tag for value, tag in doc.aria if needle in value.casefold()}
    # An element carrying BOTH <label for=...> and aria-label is still one control.
    overlap = min(len(explicit), len(aria))
    return len(explicit) + wrapping + len(aria) - overlap


def main() -> int:
    found = harvest()
    docs, everything = render_pages()
    problems: list[str] = []
    skipped: list[str] = []

    for test_id, src in sorted(set(found["get_by_test_id"])):
        if f'data-testid="{test_id}"' not in everything:
            problems.append(f"test-id '{test_id}' exists nowhere in the app   [{src}]")

    for text, src in sorted(set(found["get_by_label"])):
        per_page = {name: label_hits(doc, text) for name, doc in docs.items()}
        total = {name: n for name, n in per_page.items() if n}
        if not total:
            problems.append(f"label '{text}' matches no control on any page   [{src}]")
        else:
            ambiguous = {name: n for name, n in total.items() if n > 1}
            if ambiguous:
                problems.append(
                    f"label '{text}' is ambiguous -> strict-mode violation on {ambiguous}   [{src}]"
                )

    pools = {
        "button": [t for d in docs.values() for t in d.buttons],
        "link": [t for d in docs.values() for t in d.links],
        "heading": [t for d in docs.values() for t in d.headings],
    }
    for role, name, src in sorted(set(found["get_by_role"]), key=lambda x: (x[0], x[1] or "")):
        if name is None:
            continue
        pool = pools.get(role)
        if pool is None:
            skipped.append(f"role='{role}' name='{name}' (not statically checkable)   [{src}]")
            continue
        if not any(name.casefold() in (candidate or "").casefold() for candidate in pool):
            problems.append(f"role={role} name='{name}' matches no element   [{src}]")

    all_placeholders = {p for d in docs.values() for p in d.placeholders}
    for placeholder, src in sorted(set(found["get_by_placeholder"])):
        if placeholder not in all_placeholders:
            problems.append(f"placeholder '{placeholder}' exists nowhere   [{src}]")

    counts = {k: len(set(v)) for k, v in found.items()}
    print(
        "Locator audit: " + ", ".join(f"{n} {k.removeprefix('get_by_')}" for k, n in counts.items())
    )
    for note in skipped:
        print(f"  skipped  {note}")

    if problems:
        print("\nProblems found:")
        for problem in problems:
            print(f"  FAIL  {problem}")
            if os.environ.get("GITHUB_ACTIONS") == "true":
                print(f"::error::locator audit: {problem}")
        return 1

    print("\nOK: every locator literal resolves and no label is ambiguous.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
