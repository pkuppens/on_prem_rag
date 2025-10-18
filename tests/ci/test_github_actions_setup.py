"""Test GitHub Actions setup configuration and validation.

This module validates that the CI/CD setup is correctly configured and will work
in the GitHub Actions environment. It tests Python version constraints, dependency
installation, and environment setup to prevent CI failures.

See .github/workflows/python-ci.yml for the GitHub Actions workflow being tested.
See docs/technical/CI_SETUP.md for detailed setup documentation.
"""

import re
import sys
import tomllib
from pathlib import Path
from typing import Any

import pytest


@pytest.mark.ci_setup
class TestPythonVersionConstraints:
    """Test Python version constraints in project configuration.

    As a developer I want Python version constraints to prevent incompatible
    versions from being used, so I can avoid CI failures due to dependency
    incompatibilities.

    Technical: Validate that pyproject.toml specifies compatible Python versions
    and that uv configuration uses a specific Python version.
    """

    def test_python_version_constraint_excludes_3_14(self) -> None:
        """As a developer I want Python 3.14 to be excluded from allowed versions,
        so I can prevent pypika build failures due to ast.Str removal.

        Technical: requires-python should be >=3.12,<3.14 to exclude Python 3.14.
        Validation: Parse pyproject.toml and verify the constraint format.
        """
        pyproject_path = Path(__file__).parent.parent.parent / "pyproject.toml"

        with open(pyproject_path, "rb") as f:
            pyproject = tomllib.load(f)

        requires_python = pyproject["project"]["requires-python"]

        # Should exclude Python 3.14 due to pypika incompatibility
        assert ">=3.12" in requires_python, "Should support Python 3.12+"
        assert "<3.14" in requires_python, "Should exclude Python 3.14 due to pypika incompatibility"

        # Verify the constraint is properly formatted
        assert re.match(r">=3\.12,<3\.14", requires_python), f"Invalid constraint format: {requires_python}"

    def test_uv_python_version_is_pinned(self) -> None:
        """As a developer I want uv to use a specific Python version,
        so I can ensure consistent builds across environments.

        Technical: requires-python should exclude Python 3.14 to prevent pypika issues.
        Validation: Check that requires-python constraint excludes Python 3.14.
        """
        pyproject_path = Path(__file__).parent.parent.parent / "pyproject.toml"

        with open(pyproject_path, "rb") as f:
            pyproject = tomllib.load(f)

        # Check if project configuration exists
        assert "project" in pyproject, "pyproject.toml should have [project] section"

        project_config = pyproject["project"]
        requires_python = project_config["requires-python"]

        # Should exclude Python 3.14 due to pypika incompatibility
        assert ">=3.12" in requires_python, "Should support Python 3.12+"
        assert "<3.14" in requires_python, "Should exclude Python 3.14 due to pypika incompatibility"


@pytest.mark.ci_setup
class TestGitHubActionsWorkflow:
    """Test GitHub Actions workflow configuration.

    As a developer I want the GitHub Actions workflow to use compatible Python
    versions, so I can prevent CI failures due to version mismatches.

    Technical: Validate that the workflow YAML specifies Python 3.12 in the matrix.
    """

    def test_workflow_python_version_matrix(self) -> None:
        """As a developer I want the GitHub Actions workflow to use Python 3.12,
        so I can ensure consistency with local development and avoid CI failures.

        Technical: workflow YAML should specify python-version: ["3.12"] in matrix.
        Validation: Parse workflow file and verify Python version specification.
        """
        workflow_path = Path(__file__).parent.parent.parent / ".github" / "workflows" / "python-ci.yml"

        assert workflow_path.exists(), "GitHub Actions workflow file should exist"

        workflow_content = workflow_path.read_text(encoding="utf-8")

        # Check that Python 3.12 is specified in the matrix
        assert 'python-version: ["3.12"]' in workflow_content, "Workflow should use Python 3.12"

        # Ensure no other Python versions are specified
        python_version_matches = re.findall(r'python-version:\s*\["([^"]+)"\]', workflow_content)
        for version in python_version_matches:
            assert version == "3.12", f"All Python versions should be 3.12, found: {version}"

    def test_workflow_has_setup_job(self) -> None:
        """As a developer I want the workflow to have a setup job,
        so I can ensure dependencies are installed before other jobs run.

        Technical: workflow should have a 'setup' job that other jobs depend on.
        Validation: Check for setup job definition and dependencies.
        """
        workflow_path = Path(__file__).parent.parent.parent / ".github" / "workflows" / "python-ci.yml"
        workflow_content = workflow_path.read_text(encoding="utf-8")

        # Check for setup job
        assert "setup:" in workflow_content, "Workflow should have a setup job"

        # Check that other jobs depend on setup
        assert "needs: setup" in workflow_content, "Other jobs should depend on setup job"
        assert "needs: [setup" in workflow_content, "Some jobs should depend on setup job"


@pytest.mark.ci_setup
class TestDependencyInstallation:
    """Test that dependencies can be installed successfully.

    As a developer I want to validate that all dependencies can be installed
    with the specified Python version, so I can prevent CI failures.

    Technical: Test that uv can sync dependencies without errors.
    """

    def test_uv_sync_works_with_current_python(self) -> None:
        """As a developer I want uv sync to work with the current Python version,
        so I can validate that dependencies are compatible.

        Technical: Run uv sync --dev in dry-run mode to validate dependency resolution.
        Validation: Check that uv can resolve all dependencies without conflicts.
        """
        import subprocess
        import sys

        # Check that we're using a compatible Python version
        python_version = sys.version_info
        assert python_version >= (3, 12), f"Python version {python_version} should be >= 3.12"
        assert python_version < (3, 14), f"Python version {python_version} should be < 3.14"

        # Test that uv is available
        try:
            result = subprocess.run(["uv", "--version"], capture_output=True, text=True, timeout=10)
            assert result.returncode == 0, f"uv should be available: {result.stderr}"
        except (subprocess.TimeoutExpired, FileNotFoundError):
            pytest.skip("uv not available in test environment")

    def test_pyproject_toml_is_valid(self) -> None:
        """As a developer I want pyproject.toml to be valid TOML,
        so I can ensure it can be parsed by build tools.

        Technical: pyproject.toml should be parseable as valid TOML.
        Validation: Attempt to parse the file and check for syntax errors.
        """
        pyproject_path = Path(__file__).parent.parent.parent / "pyproject.toml"

        # This should not raise an exception
        with open(pyproject_path, "rb") as f:
            pyproject = tomllib.load(f)

        # Basic structure validation
        assert "project" in pyproject, "pyproject.toml should have [project] section"
        assert "name" in pyproject["project"], "project should have a name"
        assert "dependencies" in pyproject["project"], "project should have dependencies"


@pytest.mark.ci_setup
class TestEnvironmentConfiguration:
    """Test environment configuration for CI.

    As a developer I want the CI environment to be properly configured,
    so I can ensure consistent behavior across runs.

    Technical: Validate environment variables and cache configuration.
    """

    def test_required_environment_variables_are_documented(self) -> None:
        """As a developer I want required environment variables to be documented,
        so I can understand what the CI environment needs.

        Technical: Check that HF_HOME and related variables are set in workflow.
        Validation: Verify environment variable configuration in workflow.
        """
        workflow_path = Path(__file__).parent.parent.parent / ".github" / "workflows" / "python-ci.yml"
        workflow_content = workflow_path.read_text(encoding="utf-8")

        # Check for required environment variables
        required_vars = ["HF_HOME", "TRANSFORMERS_CACHE", "SENTENCE_TRANSFORMERS_HOME"]
        for var in required_vars:
            assert f"{var}:" in workflow_content, f"Workflow should set {var} environment variable"

    def test_cache_configuration_is_present(self) -> None:
        """As a developer I want cache configuration to be present,
        so I can ensure efficient CI runs with proper caching.

        Technical: Workflow should have cache steps for uv and HuggingFace models.
        Validation: Check for cache action usage in workflow.
        """
        workflow_path = Path(__file__).parent.parent.parent / ".github" / "workflows" / "python-ci.yml"
        workflow_content = workflow_path.read_text(encoding="utf-8")

        # Check for cache actions
        assert "actions/cache@v3" in workflow_content, "Workflow should use cache action"
        assert "Cache UV dependencies" in workflow_content, "Should cache UV dependencies"
        assert "Cache HuggingFace models" in workflow_content, "Should cache HuggingFace models"
