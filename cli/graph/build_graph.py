#!/usr/bin/env python3
from __future__ import annotations

from cli.bootstrap import bootstrap_cli
from app.modules.graph.tasks.cli import main


if __name__ == "__main__":
    bootstrap_cli()
    raise SystemExit(main())
