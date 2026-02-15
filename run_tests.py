#!/usr/bin/env python3
import io
import os
import sys
import tempfile
import unittest
from contextlib import redirect_stdout, redirect_stderr

# Patterns that should NEVER appear during a healthy bootstrap/test run.
FORBIDDEN_PATTERNS = [
    "Migration warning:",
    "Roles migration warning:",
    "no such table:",
    "sqlite3.OperationalError",
    "Traceback (most recent call last):",
]

def main() -> int:
    # Always run tests against an isolated temporary database.
    tmpdir = tempfile.mkdtemp(prefix="green_david_tests_")
    db_path = os.path.join(tmpdir, "test_app.db")
    os.environ["DB_PATH"] = db_path
    os.environ["FLASK_ENV"] = "testing"
    os.environ["ADMIN_EMAIL"] = os.environ.get("ADMIN_EMAIL", "admin@greendavid.local")
    os.environ["ADMIN_PASSWORD"] = os.environ.get("ADMIN_PASSWORD", "admin123")
    os.environ["ADMIN_NAME"] = os.environ.get("ADMIN_NAME", "Admin")

    buf = io.StringIO()
    # Run unittest discovery with output capture so we can hard-fail on warnings.
    with redirect_stdout(buf), redirect_stderr(buf):
        loader = unittest.TestLoader()
        suite = loader.discover("tests")
        runner = unittest.TextTestRunner(verbosity=2)
        result = runner.run(suite)

    output = buf.getvalue()
    # Print captured output for the user (keeps current behavior).
    sys.stdout.write(output)

    # Hard-fail on forbidden patterns even if tests themselves passed.
    lowered = output.lower()
    for pat in FORBIDDEN_PATTERNS:
        if pat.lower() in lowered:
            sys.stdout.write("\n[TESTS] FAIL: Detected forbidden pattern in output: %r\n" % pat)
            return 1

    return 0 if result.wasSuccessful() else 1

if __name__ == "__main__":
    raise SystemExit(main())
