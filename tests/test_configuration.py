"""Tests for project configuration files."""

import os

import pytest
import toml
import yaml


@pytest.mark.parametrize(
    "config_file",
    [
        "pyproject.toml",
        "ruff.toml",
        ".pre-commit-config.yaml",
    ],
)
def test_config_files_exist(config_file):
    """Test that required configuration files exist."""
    assert os.path.exists(config_file), f"{config_file} does not exist"


def test_pyproject_structure():
    """Test pyproject.toml structure and required fields."""
    with open("pyproject.toml") as f:
        config = toml.load(f)

    assert "project" in config
    assert "name" in config["project"]
    assert "version" in config["project"]
    assert "dependencies" in config["project"]


def test_ruff_configuration():
    """Test ruff.toml contains expected configurations."""
    with open("ruff.toml") as f:
        config = toml.load(f)

    assert "lint" in config
    assert "select" in config["lint"]
    assert "ignore" in config["lint"]
    assert "format" in config
    # Check format settings without specific line length requirement
    assert "indent-style" in config["format"]
    assert "quote-style" in config["format"]


def test_pre_commit_hooks():
    """Test pre-commit config contains required hooks."""
    with open(".pre-commit-config.yaml") as f:
        config = yaml.safe_load(f)

    assert isinstance(config, dict)
    assert "repos" in config
    assert isinstance(config["repos"], list)
    assert any("ruff" in repo["repo"] for repo in config["repos"])
    assert any("black" in repo["repo"] for repo in config["repos"])
