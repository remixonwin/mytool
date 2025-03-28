"""Tests for GitHub workflows."""

import os

import pytest
import yaml


@pytest.mark.parametrize(
    "workflow_file",
    [
        ".github/workflows/ci.yml",
        ".github/workflows/cd.yml",
    ],
)
def test_workflow_files_exist(workflow_file):
    """Test that required workflow files exist."""
    assert os.path.exists(workflow_file), f"{workflow_file} does not exist"


def test_ci_workflow_structure():
    """Test CI workflow structure and required fields."""
    with open(".github/workflows/ci.yml") as f:
        workflow = yaml.safe_load(f)

    assert "name" in workflow
    assert workflow["name"] == "CI"
    assert True in workflow  # YAML parses 'on' as True
    assert "jobs" in workflow
    assert "test" in workflow["jobs"]


def test_cd_workflow_structure():
    """Test CD workflow structure and required fields."""
    with open(".github/workflows/cd.yml") as f:
        workflow = yaml.safe_load(f)

    assert "name" in workflow
    assert workflow["name"] == "CD"
    assert True in workflow  # YAML parses 'on' as True
    assert "jobs" in workflow
    assert "deploy" in workflow["jobs"]


def test_ci_workflow_steps():
    """Test CI workflow contains required steps."""
    with open(".github/workflows/ci.yml") as f:
        workflow = yaml.safe_load(f)

    steps = workflow["jobs"]["test"]["steps"]
    assert any(step.get("uses", "").startswith("actions/checkout") for step in steps)
    assert any("setup-python" in step.get("uses", "") for step in steps)
    assert any("Run tests" in step.get("name", "") for step in steps)
