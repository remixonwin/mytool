"""Tests for project tracker functionality."""

import os
import subprocess
from pathlib import Path
from unittest.mock import PropertyMock, mock_open, patch

import pytest
import yaml
from jsonschema import validate

from hooks.update_project_tracker import TRACKER_SCHEMA, update_tracker


@pytest.fixture
def tracker_path(tmp_path):
    """Fixture providing path to test tracker file."""
    path = tmp_path / "project_tracker.yaml"
    yield path
    if path.exists():
        path.unlink()


def test_documentation_section_created_when_missing(tracker_path):
    """Test that documentation section is created when missing."""
    # Create minimal tracker without documentation section
    with open(tracker_path, "w") as f:
        yaml.dump(
            {
                "project": {"name": "test", "version": "1.0.0"},
                "environment": {"python_version": "3.12", "package_manager": "uv"},
                "dependencies": {"development": []},
            },
            f,
        )

    # Import and run the update function
    update_tracker(str(tracker_path))

    # Verify documentation section was added
    with open(tracker_path) as f:
        data = yaml.safe_load(f)
        assert "documentation" in data
        assert data["documentation"]["generated"] is False
        assert data["documentation"]["last_updated"] == ""
        validate(instance=data, schema=TRACKER_SCHEMA)


def test_documentation_with_missing_docs_dir(tracker_path):
    """Test documentation handling when docs directory doesn't exist."""
    # Ensure docs directory doesn't exist
    if Path("docs").exists():
        pytest.skip("docs directory exists")

    update_tracker(str(tracker_path))

    with open(tracker_path) as f:
        data = yaml.safe_load(f)
        assert data["documentation"]["generated"] is False
        assert data["documentation"]["last_updated"] == ""


def test_documentation_with_existing_docs_dir(tracker_path, tmp_path):
    """Test documentation handling when docs directory exists."""
    docs_dir = tmp_path / "docs"
    docs_dir.mkdir()
    (docs_dir / "index.md").touch()

    update_tracker(str(tracker_path))

    with open(tracker_path) as f:
        data = yaml.safe_load(f)
        assert data["documentation"]["generated"] is True
        assert data["documentation"]["last_updated"] != ""


def test_new_tracker_creation(tracker_path):
    """Test creation of new tracker file when it doesn't exist."""
    # Ensure file doesn't exist
    if tracker_path.exists():
        tracker_path.unlink()

    update_tracker(str(tracker_path))

    assert tracker_path.exists()
    with open(tracker_path) as f:
        data = yaml.safe_load(f)
        assert "project" in data
        assert "environment" in data
        assert "dependencies" in data
        assert "configuration_files" in data
        assert "source_code" in data
        assert "tests" in data
        validate(instance=data, schema=TRACKER_SCHEMA)


@pytest.fixture
def mock_git_files(monkeypatch, tmp_path):
    """Mock git ls-files output."""

    def mock_run(*args, **kwargs):
        if "ls-files" in args[0]:
            if "*.py" in args[0]:
                return subprocess.CompletedProcess(
                    args=args,
                    returncode=0,
                    stdout="src/main.py\nsrc/utils.py\ntests/test_main.py\n",
                    stderr="",
                )
            return subprocess.CompletedProcess(
                args=args,
                returncode=0,
                stdout="src/main.py\nsrc/utils.py\ntests/test_main.py\npyproject.toml\n",
                stderr="",
            )
        if "pip" in args[0] and "freeze" in args[0]:
            return subprocess.CompletedProcess(
                args=args,
                returncode=0,
                stdout="pytest==8.0.0\nruff==0.2.0\npre-commit==3.5.0\n",
                stderr="",
            )
        return subprocess.run(*args, **kwargs)

    # Create mock files
    src_dir = tmp_path / "src"
    src_dir.mkdir()
    (src_dir / "main.py").touch()
    (src_dir / "utils.py").touch()

    tests_dir = tmp_path / "tests"
    tests_dir.mkdir()
    (tests_dir / "test_main.py").touch()

    (tmp_path / "pyproject.toml").touch()

    os.chdir(tmp_path)
    monkeypatch.setattr("subprocess.run", mock_run)

    yield

    # Change back to original directory
    os.chdir(Path(__file__).parent.parent)


@pytest.fixture
def mock_installed_packages(monkeypatch):
    """Mock uv pip freeze output."""

    def mock_run(*args, **kwargs):
        if "pip" in args[0] and "freeze" in args[0]:

            class MockResult:
                stdout = "pytest==8.0.0\nruff==0.2.0\npre-commit==3.5.0"
                returncode = 0

            return MockResult()
        # Pass through other commands
        return subprocess.run(*args, **kwargs)

    monkeypatch.setattr("subprocess.run", mock_run)


def test_project_structure_tracking(tracker_path, mock_git_files):
    """Test tracking of project structure."""
    update_tracker(str(tracker_path))

    with open(tracker_path) as f:
        data = yaml.safe_load(f)
        assert "project_structure" in data
        structure = data["project_structure"]
        assert "src" in structure
        assert "main.py" in structure["src"]
        assert "utils.py" in structure["src"]


def test_dependencies_tracking(tracker_path, mock_installed_packages, mock_git_files):
    """Test tracking of project dependencies."""
    update_tracker(str(tracker_path))

    with open(tracker_path) as f:
        data = yaml.safe_load(f)
        assert "dependencies" in data
        dev_deps = data["dependencies"]["development"]
        assert any("pytest" in dep for dep in dev_deps)
        assert any("ruff" in dep for dep in dev_deps)
        assert any("pre-commit" in dep for dep in dev_deps)


def test_source_and_test_files_tracking(tracker_path, mock_git_files):
    """Test tracking of source and test files."""
    update_tracker(str(tracker_path))

    with open(tracker_path) as f:
        data = yaml.safe_load(f)
        assert "source_code" in data
        assert "tests" in data

        source_files = data["source_code"]["files"]
        test_files = data["tests"]["files"]

        assert any(file["path"] == "src/main.py" for file in source_files)
        assert any(file["path"] == "tests/test_main.py" for file in test_files)


def test_validation_error_handling(tmp_path):
    tracker_path = tmp_path / "project_tracker.yaml"
    invalid_data = {
        "project": {
            "name": "test",
            "version": "invalid.version",  # Invalid version format
        },
        "environment": {"python_version": "3.12.0", "package_manager": "uv"},
        "dependencies": {"development": []},
        "configuration_files": {"files": []},
        "documentation": {
            "generated": False,
            "last_updated": "2025-03-27",
            "tool": "pdoc",
        },
    }

    with patch("builtins.open", mock_open(read_data=yaml.dump(invalid_data))), patch(
        "os.path.exists", return_value=True
    ):
        result = update_tracker(str(tracker_path))
        assert result == 1


def test_subprocess_error_handling(tmp_path):
    tracker_path = tmp_path / "project_tracker.yaml"

    with patch("subprocess.run") as mock_run, patch(
        "os.path.exists", return_value=True
    ), patch("builtins.open", mock_open()):
        mock_run.side_effect = subprocess.CalledProcessError(1, "git ls-files")
        result = update_tracker(str(tracker_path))
        assert result == 1


def test_documentation_generated_status(tmp_path):
    tracker_path = tmp_path / "project_tracker.yaml"
    docs_dir = tmp_path / "docs"
    docs_dir.mkdir()
    (docs_dir / "index.html").write_text("test")

    mock_data = {
        "project": {"name": "test", "version": "0.1.0"},
        "environment": {"python_version": "3.12.0", "package_manager": "uv"},
        "dependencies": {"development": []},
        "configuration_files": {"files": []},
        "documentation": {
            "generated": False,
            "last_updated": "2025-03-27",
            "tool": "pdoc",
        },
    }

    with patch("os.path.exists", return_value=True), patch(
        "builtins.open", mock_open(read_data=yaml.dump(mock_data))
    ), patch("subprocess.run") as mock_run, patch(
        "pathlib.Path", return_value=docs_dir
    ):
        mock_run.return_value.stdout = ""
        mock_run.return_value.returncode = 0
        result = update_tracker(str(tracker_path))
        assert result == 0


def test_missing_optional_sections(tmp_path):
    tracker_path = tmp_path / "project_tracker.yaml"
    minimal_data = {
        "project": {"name": "test", "version": "0.1.0"},
        "environment": {"python_version": "3.12.0", "package_manager": "uv"},
        "dependencies": {"development": []},
        "configuration_files": {"files": []},
        "documentation": {
            "generated": False,
            "last_updated": "2025-03-27",
            "tool": "pdoc",
        },
    }

    with patch("builtins.open", mock_open(read_data=yaml.dump(minimal_data))), patch(
        "os.path.exists", return_value=True
    ), patch("subprocess.run") as mock_run:
        mock_run.return_value.stdout = ""
        mock_run.return_value.returncode = 0
        result = update_tracker(str(tracker_path))
        assert result == 0


def test_documentation_update_edge_cases(tmp_path):
    tracker_path = tmp_path / "project_tracker.yaml"
    docs_dir = tmp_path / "docs"
    docs_dir.mkdir()
    (docs_dir / "index.html").write_text("test")

    mock_data = {
        "project": {"name": "test", "version": "0.1.0"},
        "environment": {"python_version": "3.12.0", "package_manager": "uv"},
        "dependencies": {"development": []},
        "configuration_files": {"files": []},
        "documentation": {
            "generated": False,
            "last_updated": "2025-03-27",
            "tool": "pdoc",
        },
    }

    with patch("os.path.exists", return_value=True), patch(
        "builtins.open", mock_open(read_data=yaml.dump(mock_data))
    ), patch("subprocess.run") as mock_run, patch(
        "pathlib.Path", return_value=docs_dir
    ), patch(
        "os.path.getmtime", return_value=1711497600
    ), patch(
        "hooks.update_project_tracker.datetime"
    ) as mock_datetime:
        # Mock datetime for consistent results
        mock_datetime.now.return_value.strftime.return_value = "2025-03-27"
        mock_datetime.fromtimestamp.return_value.strftime.return_value = "2025-03-27"

        # Mock subprocess commands
        def mock_subprocess(*args, **kwargs):
            if "git" in args[0]:
                return subprocess.CompletedProcess(
                    args=args,
                    returncode=0,
                    stdout="src/pyboplate/main.py\ntests/test_main.py\n",
                    stderr="",
                )
            if "uv" in args[0]:
                return subprocess.CompletedProcess(
                    args=args, returncode=0, stdout="pytest==8.0.0\n", stderr=""
                )
            return subprocess.CompletedProcess(
                args=args, returncode=0, stdout="", stderr=""
            )

        mock_run.side_effect = mock_subprocess
        result = update_tracker(str(tracker_path))
        assert result == 0


def test_documentation_dir_error_handling(tracker_path):
    """Test error handling when docs directory has permission issues."""
    with patch("pathlib.Path.exists") as mock_exists, patch(
        "pathlib.Path.iterdir"
    ) as mock_iterdir:
        # Make exists() return True but iterdir() raise PermissionError
        mock_exists.return_value = True
        mock_iterdir.side_effect = PermissionError("Permission denied")

        # Create minimal tracker
        with open(tracker_path, "w") as f:
            yaml.dump(
                {
                    "project": {"name": "test", "version": "0.1.0"},
                    "environment": {"python_version": "3.12", "package_manager": "uv"},
                    "dependencies": {"development": []},
                    "documentation": {
                        "generated": False,
                        "last_updated": "",
                        "tool": "",
                    },
                    "configuration_files": {"files": []},
                },
                f,
            )

        result = update_tracker(str(tracker_path))
        assert result == 1


def test_file_modification_error_handling(tracker_path, mock_git_files):
    """Test error handling when file modification time can't be accessed."""
    with patch("os.path.getmtime") as mock_getmtime:
        mock_getmtime.side_effect = OSError("File access error")

        # Create minimal tracker
        with open(tracker_path, "w") as f:
            yaml.dump(
                {
                    "project": {"name": "test", "version": "0.1.0"},
                    "environment": {"python_version": "3.12", "package_manager": "uv"},
                    "dependencies": {"development": []},
                    "documentation": {
                        "generated": False,
                        "last_updated": "",
                        "tool": "",
                    },
                    "configuration_files": {"files": []},
                },
                f,
            )

        result = update_tracker(str(tracker_path))
        assert result == 1


def test_docs_dir_empty_handling(tracker_path):
    """Test handling when docs directory exists but is empty."""
    docs_dir = Path(tracker_path).parent / "docs"
    docs_dir.mkdir(exist_ok=True)

    update_tracker(str(tracker_path))

    with open(tracker_path) as f:
        data = yaml.safe_load(f)
        assert data["documentation"]["generated"] is False
        assert data["documentation"]["last_updated"] == ""


def test_git_command_error_with_retry(tracker_path):
    """Test handling of git command errors with retry logic."""
    call_count = 0

    def mock_run(*args, **kwargs):
        nonlocal call_count
        call_count += 1
        if call_count <= 1:  # Fail first attempt
            raise subprocess.CalledProcessError(1, args[0])
        # Return success on subsequent attempts
        return subprocess.CompletedProcess(args, 0, stdout="", stderr="")

    with patch("subprocess.run", side_effect=mock_run):
        result = update_tracker(str(tracker_path))
        assert result == 1  # Should still fail due to incomplete data


def test_docs_dir_stat_error(tracker_path):
    """Test error handling when docs directory stat() fails."""
    docs_dir = Path(tracker_path).parent / "docs"
    docs_dir.mkdir(exist_ok=True)

    with patch("pathlib.Path.exists") as mock_exists, patch(
        "pathlib.Path.iterdir"
    ) as mock_iterdir, patch("pathlib.Path.stat") as mock_stat:
        mock_exists.return_value = True
        mock_iterdir.return_value = [docs_dir / "index.html"]  # Simulate a file exists
        mock_stat.side_effect = OSError("Permission denied")

        # Create minimal tracker
        with open(tracker_path, "w") as f:
            yaml.dump(
                {
                    "project": {"name": "test", "version": "0.1.0"},
                    "environment": {"python_version": "3.12", "package_manager": "uv"},
                    "dependencies": {"development": []},
                    "documentation": {
                        "generated": False,
                        "last_updated": "",
                        "tool": "",
                    },
                    "configuration_files": {"files": []},
                },
                f,
            )

        result = update_tracker(str(tracker_path))
        assert result == 1


def test_git_command_failure_handling(tracker_path):
    """Test handling of multiple git command failures."""
    with patch("subprocess.run") as mock_run:

        def fail_specific_commands(*args, **kwargs):
            if "git ls-files *.py" in " ".join(args[0]):
                raise subprocess.CalledProcessError(1, args[0])
            if "git ls-files" in " ".join(args[0]):
                return subprocess.CompletedProcess(args[0], 0, stdout="", stderr="")
            return subprocess.CompletedProcess(args[0], 0, stdout="", stderr="")

        mock_run.side_effect = fail_specific_commands

        # Create minimal tracker
        with open(tracker_path, "w") as f:
            yaml.dump(
                {
                    "project": {"name": "test", "version": "0.1.0"},
                    "environment": {"python_version": "3.12", "package_manager": "uv"},
                    "dependencies": {"development": []},
                    "documentation": {
                        "generated": False,
                        "last_updated": "",
                        "tool": "",
                    },
                    "configuration_files": {"files": []},
                },
                f,
            )

        result = update_tracker(str(tracker_path))
        assert result == 1


def test_iterdir_empty_docs_dir(tracker_path):
    """Test handling when docs directory exists but is empty and iterdir() fails."""
    docs_dir = Path(tracker_path).parent / "docs"
    docs_dir.mkdir(exist_ok=True)

    with patch("pathlib.Path.exists") as mock_exists, patch(
        "pathlib.Path.iterdir"
    ) as mock_iterdir:
        mock_exists.return_value = True
        mock_iterdir.side_effect = (
            StopIteration()
        )  # Simulate empty directory with error

        result = update_tracker(str(tracker_path))
        assert result == 1


def test_docs_dir_stat_race_condition(tracker_path):
    """Test handling of race condition where docs dir exists but disappears
    during processing."""
    docs_dir = Path(tracker_path).parent / "docs"
    docs_dir.mkdir(exist_ok=True)
    exists_call_count = 0

    def mock_exists(self):
        nonlocal exists_call_count
        exists_call_count += 1
        if exists_call_count == 1:
            return True
        return False

    with patch.object(Path, "exists", mock_exists), patch(
        "pathlib.Path.iterdir"
    ) as mock_iterdir:
        # First exists() returns True, but dir disappears before iterdir()
        mock_iterdir.side_effect = FileNotFoundError("Directory no longer exists")
        update_tracker(str(tracker_path))
        with open(tracker_path) as f:
            data = yaml.safe_load(f)
            assert data["documentation"]["generated"] is False
            assert data["documentation"]["last_updated"] == ""


def test_docs_dir_complex_structure(tracker_path):
    """Test handling of complex documentation directory structure with mixed content."""
    # Create initial tracker file
    initial_data = {
        "project": {"name": "test", "version": "0.1.0"},
        "environment": {"python_version": "3.12", "package_manager": "uv"},
        "dependencies": {"development": []},
        "documentation": {"generated": False, "last_updated": "", "tool": ""},
        "configuration_files": {"files": []},
    }
    with open(tracker_path, "w") as f:
        yaml.dump(initial_data, f)

    # Set up docs directory structure
    docs_dir = Path(tracker_path).parent / "docs"
    docs_dir.mkdir(exist_ok=True)
    (docs_dir / "empty_dir").mkdir()
    (docs_dir / "index.html").touch()

    # Create nested structure
    nested_dir = docs_dir / "nested"
    nested_dir.mkdir()
    (nested_dir / "api.md").touch()

    mock_time = 1711497600  # 2024-03-27 00:00:00

    with patch("os.path.getmtime") as mock_getmtime, patch(
        "hooks.update_project_tracker.datetime"
    ) as mock_datetime:
        # Mock the modification time for consistent testing
        mock_getmtime.return_value = mock_time
        mock_datetime.fromtimestamp.return_value.strftime.return_value = "2024-03-27"

        update_tracker(str(tracker_path))

        with open(tracker_path) as f:
            data = yaml.safe_load(f)
            assert data["documentation"]["generated"] is True
            assert data["documentation"]["last_updated"] == "2024-03-27"


def test_docs_dir_complex_yaml_error(tracker_path):
    """Test handling of YAML errors during tracker updates."""
    docs_dir = Path(tracker_path).parent / "docs"
    docs_dir.mkdir(exist_ok=True)
    (docs_dir / "index.html").touch()

    with patch("builtins.open") as mock_open:
        # First call to open() returns valid data
        mock_open.side_effect = [
            mock_open(
                read_data=yaml.dump(
                    {
                        "project": {"name": "test", "version": "0.1.0"},
                        "environment": {
                            "python_version": "3.12",
                            "package_manager": "uv",
                        },
                        "dependencies": {"development": []},
                        "documentation": {
                            "generated": False,
                            "last_updated": "",
                            "tool": "",
                        },
                        "configuration_files": {"files": []},
                    }
                )
            ).return_value,
            # Second call raises yaml error
            yaml.YAMLError("Invalid YAML"),
        ]

        result = update_tracker(str(tracker_path))
        assert result == 1


def test_docs_dir_path_error(tracker_path):
    """Test handling of path-related errors in documentation handling."""
    with patch("pathlib.Path.parent", new_callable=PropertyMock) as mock_parent, patch(
        "subprocess.run"
    ) as mock_run:
        # Mock parent property to raise error
        mock_parent.side_effect = RuntimeError("Path error")
        # Mock subprocess to prevent other errors
        mock_run.return_value = subprocess.CompletedProcess([], 0, stdout="", stderr="")

        # Create minimal tracker
        with open(tracker_path, "w") as f:
            yaml.dump(
                {
                    "project": {"name": "test", "version": "0.1.0"},
                    "environment": {"python_version": "3.12", "package_manager": "uv"},
                    "dependencies": {"development": []},
                    "documentation": {
                        "generated": False,
                        "last_updated": "",
                        "tool": "",
                    },
                    "configuration_files": {"files": []},
                },
                f,
            )

        with patch(
            "pathlib.Path.exists", return_value=True
        ):  # Ensure path.exists returns True
            result = update_tracker(str(tracker_path))
            assert result == 1


def test_git_command_output_error(tracker_path):
    """Test handling of invalid git command output."""
    with patch("subprocess.run") as mock_run:

        def mock_subprocess(*args, **kwargs):
            if "git ls-files" in " ".join(args[0]):
                raise ValueError("Invalid path characters in git output")
            return subprocess.CompletedProcess(args[0], 0, stdout="", stderr="")

        mock_run.side_effect = mock_subprocess

        # Create minimal tracker
        with open(tracker_path, "w") as f:
            yaml.dump(
                {
                    "project": {"name": "test", "version": "0.1.0"},
                    "environment": {"python_version": "3.12", "package_manager": "uv"},
                    "dependencies": {"development": []},
                    "documentation": {
                        "generated": False,
                        "last_updated": "",
                        "tool": "",
                    },
                    "configuration_files": {"files": []},
                },
                f,
            )

        result = update_tracker(str(tracker_path))
        assert result == 1
