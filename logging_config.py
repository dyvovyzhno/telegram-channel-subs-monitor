"""Logging setup — keep the config in one place and call `setup_logging()` once at startup.

Design: plain stdlib `logging` going to stderr. journald captures stderr,
tags each line with its own timestamp and PID, and adds the unit name —
the Python-side format adds the logger name and level, which is what
you actually want to grep.

No JSON formatter and no structlog: this is a single process with one
destination. Structured logging pays off when you're shipping to Loki
or Datadog; for `journalctl -u ...` text is strictly easier to read.
"""

import logging
import sys


def setup_logging(level: str = "INFO") -> None:
    """Configure the root logger. Idempotent — calling twice does not duplicate handlers."""
    root = logging.getLogger()
    root.setLevel(level.upper())

    # Clear any handlers a previous call may have installed, so re-initialisation
    # (e.g. tests, REPL) does not produce duplicated lines.
    for handler in list(root.handlers):
        root.removeHandler(handler)

    handler = logging.StreamHandler(sys.stderr)
    handler.setFormatter(
        logging.Formatter(
            fmt="%(asctime)s %(levelname)-7s %(name)s: %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )
    )
    root.addHandler(handler)
