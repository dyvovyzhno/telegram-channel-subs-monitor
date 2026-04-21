# TODO

Nice-to-have items intentionally deferred. Single-maintainer project — these become relevant if the scope grows (second contributor, public release, CI policy, release tracking).

## Tooling

- **`pre-commit` hooks** — run `ruff` (format + lint), `pyright`, `detect-secrets` on every commit. Prevents accidental leaks of tokens/keys and keeps the tree ruff-clean without thinking.
- **GitHub Actions CI** — on push/PR: `ruff check`, `pyright`, `pytest`. Currently all checks are local-only.
- **Pyright strict mode** — currently runs in `basic` mode (clean). Strict reports ~196 errors, mostly missing parameter/return annotations. Most natural moment to turn on: after the src-layout refactor (PR #5 in the main plan), because new code there will be typed from day one and the remaining debt will be mostly in the Telethon wrapper.

## Project meta

- **`CONTRIBUTING.md`** — setup / dev loop / PR conventions. Add when a second contributor appears.
- **`CHANGELOG.md`** — user-facing release notes. Add when there are real users / tagged releases.

## How to pick up an item

Each bullet is self-contained. Pull one into a dedicated PR; no dependencies between them.
