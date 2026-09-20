#!/usr/bin/env python3
"""Entry point for the AI configuration toolchain.

    python scripts/ai.py sync            generate model entry points from .ai/
    python scripts/ai.py sync --check    fail if generated files are stale (CI)
    python scripts/ai.py check           validate rules, docs, and todo consistency
    python scripts/ai.py init <target>   adopt the template in another project

No third-party dependencies: a bare Python 3.8+ interpreter is enough.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from aitool.cli import main  # noqa: E402

if __name__ == "__main__":
    sys.exit(main())
