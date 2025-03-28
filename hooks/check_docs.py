#!/usr/bin/env python3
"""Pre-commit hook to verify documentation is up-to-date."""

import shutil
import subprocess
import sys
from pathlib import Path


def normalize_line_endings(path: Path) -> None:
    """Normalize line endings in HTML and JS files to Unix style (LF)."""
    for file in path.rglob("*"):
        if file.suffix.lower() in (".html", ".js"):
            content = file.read_text()
            normalized = content.replace("\r\n", "\n")
            if not normalized.endswith("\n"):
                normalized += "\n"
            file.write_text(normalized)


def main():
    # Generate fresh documentation
    docs_dir = Path("docs")
    if docs_dir.exists():
        shutil.rmtree(docs_dir)
    docs_dir.mkdir(exist_ok=True)

    try:
        subprocess.run(
            ["pdoc", "-o", "docs/", "src/"], check=True, capture_output=True, text=True
        )
        # Normalize line endings in generated files
        normalize_line_endings(docs_dir)
        return 0
    except subprocess.CalledProcessError as e:
        print("Error generating documentation:")
        print(e.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
