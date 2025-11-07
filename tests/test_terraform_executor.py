"""
Tests for the Terraform executor.

Tests the TerraformExecutor's ability to run Terraform commands and parse outputs.
Uses mocked subprocess calls to avoid actual Terraform execution.
"""

import json
import subprocess
from unittest.mock import Mock, patch

import pytest

from capabilities.databricks import TerraformExecutor, TerraformFiles


class TestTerraformExecutor:
    """Tests for TerraformExecutor class."""

    @pytest.fixture
    def sample_terraform_files(self):
        """Create sample Terraform files for testing."""
        return TerraformFiles(
            provider_tf="provider terraform config",
            main_tf="main terraform config",
            variables_tf="variables config",
            outputs_tf="outputs config",
            terraform_tfvars="tfvars config",
        )

    @pytest.fixture
    def mock_subprocess_success(self):
        """Mock successful subprocess.run calls."""
        with patch("capabilities.databricks.terraform_executor.subprocess.run") as mock_run:
            # Default successful response
            mock_run.return_value = Mock(
                returncode=0,
                stdout="Success",
                stderr="",
            )
            yield mock_run

    def test_executor_initialization(self):
        """Test TerraformExecutor initialization."""
        executor = TerraformExecutor(timeout_seconds=600)
        assert executor.timeout_seconds == 600

    def test_executor_uses_default_timeout(self):
        """Test that executor uses Config timeout by default."""
        executor = TerraformExecutor()
        assert executor.timeout_seconds > 0

    def test_successful_deployment_dry_run(
        self, sample_terraform_files, mock_subprocess_success, tmp_path
    ):
        """Test successful dry-run deployment (plan only)."""
        executor = TerraformExecutor()

        result = executor.execute_deployment(
            terraform_files=sample_terraform_files,
            working_dir=tmp_path,
            dry_run=True,
        )

        assert result.success is True
        assert result.terraform_plan is not None
        assert result.workspace_url is None  # No apply in dry-run
        assert result.deployment_time_seconds is not None
        assert result.deployment_time_seconds >= 0

        # Verify init and plan were called, but not apply
        calls = [call[0][0] for call in mock_subprocess_success.call_args_list]
        assert any("init" in call for call in calls)
        assert any("plan" in call for call in calls)
        assert not any("apply" in call for call in calls)

    def test_successful_deployment_with_auto_approve(
        self, sample_terraform_files, tmp_path
    ):
        """Test successful deployment with auto-approve."""
        with patch("capabilities.databricks.terraform_executor.subprocess.run") as mock_run:
            # Mock successful responses for all commands
            mock_run.side_effect = [
                # terraform init
                Mock(returncode=0, stdout="Initialized", stderr=""),
                # terraform plan
                Mock(returncode=0, stdout="Plan: 3 to add", stderr=""),
                # terraform apply
                Mock(returncode=0, stdout="Apply complete!", stderr=""),
                # terraform output
                Mock(
                    returncode=0,
                    stdout=json.dumps({
                        "workspace_url": {"value": "https://adb-123.azuredatabricks.net"},
                        "workspace_id": {"value": "/subscriptions/..."},
                        "resource_group_name": {"value": "rg-test"},
                    }),
                    stderr="",
                ),
            ]

            executor = TerraformExecutor()
            result = executor.execute_deployment(
                terraform_files=sample_terraform_files,
                working_dir=tmp_path,
                auto_approve=True,
            )

            assert result.success is True
            assert result.workspace_url == "https://adb-123.azuredatabricks.net"
            assert result.workspace_id == "/subscriptions/..."
            assert result.resource_group_name == "rg-test"
            assert result.terraform_outputs is not None

    def test_init_failure(self, sample_terraform_files, tmp_path):
        """Test handling of terraform init failure."""
        with patch("capabilities.databricks.terraform_executor.subprocess.run") as mock_run:
            mock_run.return_value = Mock(
                returncode=1,
                stdout="",
                stderr="Error: Failed to initialize",
            )

            executor = TerraformExecutor()
            result = executor.execute_deployment(
                terraform_files=sample_terraform_files,
                working_dir=tmp_path,
                auto_approve=True,
            )

            assert result.success is False
            assert result.error_message is not None
            assert "init failed" in result.error_message
            assert "Failed to initialize" in result.error_message

    def test_plan_failure(self, sample_terraform_files, tmp_path):
        """Test handling of terraform plan failure."""
        with patch("capabilities.databricks.terraform_executor.subprocess.run") as mock_run:
            mock_run.side_effect = [
                # terraform init succeeds
                Mock(returncode=0, stdout="Initialized", stderr=""),
                # terraform plan fails
                Mock(
                    returncode=1,
                    stdout="",
                    stderr="Error: Invalid configuration",
                ),
            ]

            executor = TerraformExecutor()
            result = executor.execute_deployment(
                terraform_files=sample_terraform_files,
                working_dir=tmp_path,
                auto_approve=True,
            )

            assert result.success is False
            assert result.error_message is not None
            assert "plan failed" in result.error_message
            assert "Invalid configuration" in result.error_message

    def test_apply_failure(self, sample_terraform_files, tmp_path):
        """Test handling of terraform apply failure."""
        with patch("capabilities.databricks.terraform_executor.subprocess.run") as mock_run:
            mock_run.side_effect = [
                # terraform init succeeds
                Mock(returncode=0, stdout="Initialized", stderr=""),
                # terraform plan succeeds
                Mock(returncode=0, stdout="Plan: 3 to add", stderr=""),
                # terraform apply fails
                Mock(
                    returncode=1,
                    stdout="",
                    stderr="Error: Resource already exists",
                ),
            ]

            executor = TerraformExecutor()
            result = executor.execute_deployment(
                terraform_files=sample_terraform_files,
                working_dir=tmp_path,
                auto_approve=True,
            )

            assert result.success is False
            assert result.error_message is not None
            assert "apply failed" in result.error_message
            assert "Resource already exists" in result.error_message

    def test_timeout_handling(self, sample_terraform_files, tmp_path):
        """Test handling of command timeout."""
        with patch("capabilities.databricks.terraform_executor.subprocess.run") as mock_run:
            mock_run.side_effect = subprocess.TimeoutExpired(
                cmd="terraform init", timeout=10
            )

            executor = TerraformExecutor(timeout_seconds=10)
            result = executor.execute_deployment(
                terraform_files=sample_terraform_files,
                working_dir=tmp_path,
                auto_approve=True,
            )

            assert result.success is False
            assert result.error_message is not None
            assert "timeout" in result.error_message.lower()

    def test_writes_terraform_files_to_disk(
        self, sample_terraform_files, mock_subprocess_success, tmp_path
    ):
        """Test that Terraform files are written to disk."""
        executor = TerraformExecutor()

        executor.execute_deployment(
            terraform_files=sample_terraform_files,
            working_dir=tmp_path,
            dry_run=True,
        )

        # Check all files were written
        assert (tmp_path / "provider.tf").exists()
        assert (tmp_path / "main.tf").exists()
        assert (tmp_path / "variables.tf").exists()
        assert (tmp_path / "outputs.tf").exists()
        assert (tmp_path / "terraform.tfvars").exists()

        # Check content
        assert (tmp_path / "main.tf").read_text() == "main terraform config"

    def test_parse_terraform_outputs(self, tmp_path):
        """Test parsing of terraform output JSON."""
        with patch("capabilities.databricks.terraform_executor.subprocess.run") as mock_run:
            mock_run.return_value = Mock(
                returncode=0,
                stdout=json.dumps({
                    "workspace_url": {"value": "https://test.databricks.net"},
                    "cluster_id": {"value": "cluster-123"},
                    "region": {"value": "eastus"},
                }),
                stderr="",
            )

            executor = TerraformExecutor()
            outputs = executor._parse_terraform_outputs(tmp_path)

            assert outputs["workspace_url"] == "https://test.databricks.net"
            assert outputs["cluster_id"] == "cluster-123"
            assert outputs["region"] == "eastus"

    def test_parse_terraform_outputs_failure(self, tmp_path):
        """Test handling of terraform output parsing failure."""
        with patch("capabilities.databricks.terraform_executor.subprocess.run") as mock_run:
            mock_run.return_value = Mock(
                returncode=1,
                stdout="",
                stderr="No state file",
            )

            executor = TerraformExecutor()
            outputs = executor._parse_terraform_outputs(tmp_path)

            # Should return empty dict on failure
            assert outputs == {}

    def test_parse_terraform_outputs_invalid_json(self, tmp_path):
        """Test handling of invalid JSON from terraform output."""
        with patch("capabilities.databricks.terraform_executor.subprocess.run") as mock_run:
            mock_run.return_value = Mock(
                returncode=0,
                stdout="invalid json {",
                stderr="",
            )

            executor = TerraformExecutor()
            outputs = executor._parse_terraform_outputs(tmp_path)

            # Should return empty dict on JSON parse error
            assert outputs == {}

    def test_working_directory_created(
        self, sample_terraform_files, mock_subprocess_success, tmp_path
    ):
        """Test that working directory is created if it doesn't exist."""
        nested_dir = tmp_path / "nested" / "dir"

        executor = TerraformExecutor()
        executor.execute_deployment(
            terraform_files=sample_terraform_files,
            working_dir=nested_dir,
            dry_run=True,
        )

        assert nested_dir.exists()
        assert nested_dir.is_dir()

    def test_destroy_deployment_with_auto_approve(self, tmp_path):
        """Test successful destroy with auto-approve."""
        with patch("capabilities.databricks.terraform_executor.subprocess.run") as mock_run:
            mock_run.return_value = Mock(
                returncode=0,
                stdout="Destroy complete!",
                stderr="",
            )

            executor = TerraformExecutor()
            result = executor.destroy_deployment(
                working_dir=tmp_path,
                auto_approve=True,
            )

            assert result.success is True
            assert result.deployment_time_seconds is not None
            assert result.deployment_time_seconds >= 0

            # Verify destroy was called
            mock_run.assert_called_once()
            args = mock_run.call_args[0][0]
            assert "destroy" in args
            assert "-auto-approve" in args

    def test_destroy_deployment_failure(self, tmp_path):
        """Test handling of destroy failure."""
        with patch("capabilities.databricks.terraform_executor.subprocess.run") as mock_run:
            mock_run.return_value = Mock(
                returncode=1,
                stdout="",
                stderr="Error: Resource locked",
            )

            executor = TerraformExecutor()
            result = executor.destroy_deployment(
                working_dir=tmp_path,
                auto_approve=True,
            )

            assert result.success is False
            assert result.error_message is not None
            assert "destroy failed" in result.error_message.lower()
            assert "Resource locked" in result.error_message

    def test_deployment_tracks_time(
        self, sample_terraform_files, mock_subprocess_success, tmp_path
    ):
        """Test that deployment time is tracked."""
        executor = TerraformExecutor()

        result = executor.execute_deployment(
            terraform_files=sample_terraform_files,
            working_dir=tmp_path,
            dry_run=True,
        )

        assert result.deployment_time_seconds is not None
        assert result.deployment_time_seconds >= 0

    def test_run_terraform_command_captures_output(self, tmp_path):
        """Test that terraform command output is captured."""
        with patch("capabilities.databricks.terraform_executor.subprocess.run") as mock_run:
            mock_run.return_value = Mock(
                returncode=0,
                stdout="Command output",
                stderr="Warning message",
            )

            executor = TerraformExecutor()
            result = executor._run_terraform_command(
                ["terraform", "version"],
                working_dir=tmp_path,
            )

            assert result.returncode == 0
            assert result.stdout == "Command output"
            assert result.stderr == "Warning message"

    def test_unexpected_exception_handling(
        self, sample_terraform_files, tmp_path
    ):
        """Test handling of unexpected exceptions."""
        with patch("capabilities.databricks.terraform_executor.subprocess.run") as mock_run:
            mock_run.side_effect = Exception("Unexpected error")

            executor = TerraformExecutor()
            result = executor.execute_deployment(
                terraform_files=sample_terraform_files,
                working_dir=tmp_path,
                auto_approve=True,
            )

            assert result.success is False
            assert result.error_message is not None
            assert "Unexpected error" in result.error_message
