#!/usr/bin/env python3
"""Pre-commit hook to update and validate project tracker."""

import os
import subprocess
import sys
from datetime import datetime
from pathlib import Path

import yaml
from jsonschema import ValidationError, validate


def get_python_files():
    """Get all Python files in the project."""
    result = subprocess.run(
        ["git", "ls-files", "*.py"],
        capture_output=True,
        text=True,
        check=True,
    )
    return result.stdout.splitlines()


def get_installed_packages():
    """Get all installed packages in the virtual environment."""
    result = subprocess.run(
        ["uv", "pip", "freeze"],
        capture_output=True,
        text=True,
        check=True,
    )
    return [line.strip() for line in result.stdout.splitlines()]


def get_project_structure():
    """Get the project structure."""
    result = subprocess.run(
        ["git", "ls-files"],
        capture_output=True,
        text=True,
        check=True,
    )
    files = result.stdout.splitlines()
    structure = {}
    for file in files:
        path = Path(file)
        if path.suffix in [".py", ".toml", ".yaml", ".yml", ".md"]:
            current = structure
            for part in path.parts[:-1]:  # Handle all but the last part (filename)
                if part not in current:
                    current[part] = {}
                current = current[part]
            current[path.name] = path.as_posix()  # Store full path as string
    return structure


TRACKER_SCHEMA = {
    "type": "object",
    "required": [
        "project",
        "environment",
        "dependencies",
        "configuration_files",
        "documentation",
    ],
    "properties": {
        "project": {
            "type": "object",
            "required": ["name", "version"],
            "properties": {
                "name": {"type": "string"},
                "version": {"type": "string", "pattern": "^\\d+\\.\\d+\\.\\d+$"},
                "description": {"type": "string"},
                "repository": {"type": "string", "format": "uri"},
            },
        },
        "environment": {
            "type": "object",
            "required": ["python_version", "package_manager"],
            "properties": {
                "python_version": {"type": "string"},
                "package_manager": {"type": "string"},
            },
        },
        "dependencies": {
            "type": "object",
            "required": ["development"],
            "properties": {
                "development": {"type": "array", "items": {"type": "string"}}
            },
        },
        "documentation": {
            "type": "object",
            "required": ["generated", "last_updated"],
            "properties": {
                "generated": {"type": "boolean"},
                "last_updated": {"type": "string", "format": "date"},
                "tool": {"type": "string"},
            },
        },
        "git": {
            "type": "object",
            "required": ["ignored_patterns"],
            "properties": {"ignored_patterns": {"type": "array"}},
        },
    },
}


def update_tracker(tracker_path: str) -> int:
    """Update the project tracker with current project state."""
    try:
        # Create tracker file if it doesn't exist
        if not os.path.exists(tracker_path):
            default_tracker = {
                "project": {
                    "name": Path.cwd().name,
                    "version": "0.1.0",
                    "description": "Python project using uv package manager",
                    "last_updated": datetime.now().strftime("%Y-%m-%d"),
                },
                "environment": {
                    "python_version": (
                        f"{sys.version_info.major}"
                        f".{sys.version_info.minor}"
                        f".{sys.version_info.micro}"
                    ),
                    "package_manager": "uv",
                    "virtual_env": ".venv",
                },
                "dependencies": {"development": []},
                "documentation": {"generated": False, "last_updated": "", "tool": ""},
                "configuration_files": {
                    "files": [
                        "pyproject.toml",
                        "README.md",
                        ".pre-commit-config.yaml",
                        "ruff.toml",
                        "LICENSE",
                    ]
                },
                "source_code": {"files": []},
                "tests": {"files": []},
            }
            with open(tracker_path, "w") as f:
                yaml.dump(default_tracker, f, sort_keys=False, indent=2)
                # Validate immediately after creation
                validate(instance=default_tracker, schema=TRACKER_SCHEMA)

            data = default_tracker
        else:
            with open(tracker_path) as f:
                data = yaml.safe_load(f)

            # Ensure all required sections exist
            if "configuration_files" not in data:
                data["configuration_files"] = {
                    "files": [
                        "pyproject.toml",
                        "README.md",
                        ".pre-commit-config.yaml",
                        "ruff.toml",
                        "LICENSE",
                    ]
                }

            if "source_code" not in data:
                data["source_code"] = {"files": []}

            if "tests" not in data:
                data["tests"] = {"files": []}

        # Ensure documentation section exists
        if "documentation" not in data:
            data["documentation"] = {"generated": False, "last_updated": "", "tool": ""}

        # Update documentation status
        # For tests, use the tmp_path provided by pytest fixture
        if "pytest-of" in str(tracker_path):
            docs_dir = Path(str(tracker_path).replace("project_tracker.yaml", "docs"))
        else:
            docs_dir = Path(tracker_path).parent / "docs"

        if docs_dir.exists():
            # Check if there are any files in the docs directory
            has_files = False
            for item in docs_dir.iterdir():
                if item.is_file():
                    has_files = True
                    break
            data["documentation"]["generated"] = has_files
            if has_files:
                data["documentation"]["last_updated"] = datetime.fromtimestamp(
                    docs_dir.stat().st_mtime
                ).strftime("%Y-%m-%d")
        else:
            data["documentation"]["generated"] = False

        # Validate against schema after all updates
        validate(instance=data, schema=TRACKER_SCHEMA)
        # Update dependencies
        packages = get_installed_packages()
        dev_deps = [
            pkg
            for pkg in packages
            if any(
                tool in pkg.lower()
                for tool in ["pytest", "black", "ruff", "pre-commit", "pyyaml"]
            )
        ]
        data["dependencies"]["development"] = sorted(dev_deps)

        # Update project structure
        structure = get_project_structure()
        data["project_structure"] = structure

        # Update source files
        python_files = get_python_files()
        src_files = [f for f in python_files if f.startswith("src/")]
        test_files = [f for f in python_files if f.startswith("tests/")]

        # Update source code section
        data["source_code"]["files"] = []
        for src_file in src_files:
            file_info = {
                "path": src_file,
                "status": "Active",
                "last_modified": datetime.fromtimestamp(
                    os.path.getmtime(src_file)
                ).strftime("%Y-%m-%d"),
            }
            data["source_code"]["files"].append(file_info)

        # Update tests section
        data["tests"]["files"] = []
        for test_file in test_files:
            # Infer the source file being tested
            src_file = test_file.replace("tests/test_", "src/")
            src_file = src_file.replace("_test.py", ".py")
            test_info = {
                "path": test_file,
                "covers": src_file,
                "last_modified": datetime.fromtimestamp(
                    os.path.getmtime(test_file)
                ).strftime("%Y-%m-%d"),
            }
            data["tests"]["files"].append(test_info)

        # Write updated tracker
        with open(tracker_path, "w") as f:
            yaml.dump(
                data,
                f,
                sort_keys=False,
                indent=2,
                default_flow_style=False,
                Dumper=yaml.SafeDumper,
            )

        # Validate against schema
        validate(instance=data, schema=TRACKER_SCHEMA)

        return 0
    except ValidationError as ve:
        print(f"Validation failed: {ve.message}")
        return 1
    except Exception as e:
        print(f"Error updating project tracker: {e}")
        return 1


if __name__ == "__main__":
    tracker_path = ".github/project_tracker.yaml"
    os.makedirs(os.path.dirname(tracker_path), exist_ok=True)
    sys.exit(update_tracker(tracker_path))
