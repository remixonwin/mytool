#!/usr/bin/env python3
"""Pre-commit hook to verify documentation is up-to-date."""

import shutil
import subprocess
import sys
from pathlib import Path


def normalize_file_content(path: Path) -> None:
    """Normalize line endings and whitespace in HTML and JS files."""
    for file in path.rglob("*"):
        if file.suffix in (".html", ".js"):
            # Read file in binary mode to preserve line endings
            content = file.read_bytes()
            # Convert Windows (CRLF) to Unix (LF) line endings
            normalized = content.replace(b"\r\n", b"\n")
            # Split into lines and strip trailing whitespace
            lines = [line.rstrip() for line in normalized.rstrip(b"\n").split(b"\n")]
            # Ensure file ends with exactly one newline
            content = b"\n".join(lines) + b"\n"
            file.write_bytes(content)


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
        # Normalize file content
        normalize_file_content(docs_dir)
        return 0
    except subprocess.CalledProcessError as e:
        print("Error generating documentation:")
        print(e.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
