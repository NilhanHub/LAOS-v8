from __future__ import annotations

import json
import shutil
import subprocess
from pathlib import Path

BASELINE = 107


def main() -> int:
    root = Path(__file__).resolve().parents[1]
    uv = shutil.which("uv")
    if not uv:
        print(json.dumps({"status": "FAIL", "error": "uv unavailable"}))
        return 1
    completed = subprocess.run(  # noqa: S603 - resolved uv and fixed linter arguments
        [uv, "run", "--frozen", "ruff", "check", ".", "--output-format", "json"],
        cwd=root,
        capture_output=True,
        check=False,
    )
    try:
        diagnostics = json.loads(completed.stdout)
    except ValueError:
        print(json.dumps({"status": "FAIL", "error": "ruff output invalid"}))
        return 1
    passed = isinstance(diagnostics, list) and len(diagnostics) <= BASELINE
    print(
        json.dumps(
            {
                "status": "PASS" if passed else "FAIL",
                "diagnostic_count": len(diagnostics) if isinstance(diagnostics, list) else None,
                "baseline_ceiling": BASELINE,
            },
            indent=2,
        )
    )
    return 0 if passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
