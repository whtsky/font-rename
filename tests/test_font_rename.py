"""Focused CLI tests for font-rename."""

import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent


def test_missing_path_is_an_error():
    """A path that does not exist must fail loudly, not exit 0 as 'ignored'."""
    proc = subprocess.run(
        [sys.executable, "font_rename.py", "no-such-file.ttf"],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
    )
    assert proc.returncode != 0
    assert "no-such-file.ttf" in proc.stderr
