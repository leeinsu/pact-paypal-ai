#!/bin/sh
set -eu
cd "$(dirname "$0")"
exec python3 -B - <<'PY'
import json
import os
import sys
import unittest
from pathlib import Path

suite = unittest.TestSuite()
skipped = []
try:
    for directory in ("acceptance", "tests"):
        root = Path(directory)
        if not root.is_dir():
            continue
        for test_file in root.rglob("test*.py"):
            for parent in test_file.relative_to(root).parents:
                package_path = root / parent
                if not (package_path / "__init__.py").is_file():
                    raise ValueError(f"Test package requires __init__.py: {package_path}")
        suite.addTests(unittest.TestLoader().discover(directory, top_level_dir="."))
    result = unittest.TextTestRunner(verbosity=2).run(suite)
    skipped = [str(test) for test, _ in result.skipped]
    executed = result.testsRun - len(skipped)
    failures = len(result.failures) + len(result.errors)
    passed = result.wasSuccessful() and executed > 0 and not skipped
except Exception as error:
    print(f"Test collection failed: {error}", file=sys.stderr)
    executed, failures, passed = 0, 1, False
if executed == 0:
    print("Verification failed: no tests executed.", file=sys.stderr)
if result_path := os.environ.get("DEVFLOW_TEST_RESULT"):
    Path(result_path).write_text(json.dumps({
        "executed": executed,
        "skipped": skipped,
        "failures": failures,
        "failure_class": "none" if passed else "implementation",
    }))
raise SystemExit(0 if passed else 1)
PY
