"""
Tests for the Infrastructure Agent orchestrator.

Tests the InfrastructureAgent's ability to orchestrate the full pipeline
from natural language to deployed infrastructure.
"""

from pathlib import Path
from unittest.mock import Mock

import pytest

from agent import InfrastructureAgent
from capabilities.databricks import (
    DeploymentResult,
    InfrastructureDecision,
    InfrastructureRequest,
    TerraformFiles,
)


class TestInfrastructureAgent:
    """Tests for InfrastructureAgent class."""

    @pytest.fixture
    def mock_components(self):
        """Create mocked components for testing."""
        mock_intent = Mock()
        mock_decision = Mock()
        mock_generator = Mock()
        mock_executor = Mock()

        # Setup default successful responses
        mock_intent.recognize_intent.return_value = InfrastructureRequest(
            workspace_name="test-workspace",
            team="test-team",
            environment="dev",
            region="eastus",
            enable_gpu=False,
            workload_type="data_engineering",
        )

        mock_decision.make_decision.return_value = InfrastructureDecision(
            workspace_name="test-workspace",
            resource_group_name="rg-test-workspace",
            region="eastus",
            databricks_sku="standard",
            min_workers=1,
            max_workers=3,
            driver_instance_type="Standard_DS3_v2",
            worker_instance_type="Standard_DS3_v2",
            spark_version="13.3.x-scala2.12",
            autotermination_minutes=60,
            enable_gpu=False,
            estimated_monthly_cost=500.0,
            cost_breakdown={"compute": 400, "storage": 100},
            justification="Standard dev configuration",
        )

        mock_generator.generate.return_value = TerraformFiles(
            provider_tf="provider config",
            main_tf="main config",
            variables_tf="variables config",
            outputs_tf="outputs config",
            terraform_tfvars="tfvars config",
        )

        mock_executor.execute_deployment.return_value = DeploymentResult(
            success=True,
            workspace_url="https://adb-123.azuredatabricks.net",
            workspace_id="/subscriptions/test/workspaces/test",
            resource_group_name="rg-test-workspace",
            deployment_time_seconds=300.0,
            terraform_plan="Plan: 5 to add",
            terraform_outputs={"workspace_url": "https://adb-123.azuredatabricks.net"},
            error_message=None,
        )

        return {
            "intent": mock_intent,
            "decision": mock_decision,
            "generator": mock_generator,
            "executor": mock_executor,
        }

    def test_agent_initialization_defaults(self):
        """Test agent initializes with default components."""
        agent = InfrastructureAgent()

        assert agent.intent_recognizer is not None
        assert agent.decision_engine is not None
        assert agent.terraform_generator is not None
        assert agent.terraform_executor is not None
        assert agent.working_dir is None

    def test_agent_initialization_custom_components(self, mock_components):
        """Test agent initializes with custom components."""
        agent = InfrastructureAgent(
            intent_recognizer=mock_components["intent"],
            decision_engine=mock_components["decision"],
            terraform_generator=mock_components["generator"],
            terraform_executor=mock_components["executor"],
        )

        assert agent.intent_recognizer == mock_components["intent"]
        assert agent.decision_engine == mock_components["decision"]
        assert agent.terraform_generator == mock_components["generator"]
        assert agent.terraform_executor == mock_components["executor"]

    def test_successful_provision_with_auto_approve(self, mock_components):
        """Test successful end-to-end provisioning with auto-approve."""
        agent = InfrastructureAgent(
            intent_recognizer=mock_components["intent"],
            decision_engine=mock_components["decision"],
            terraform_generator=mock_components["generator"],
            terraform_executor=mock_components["executor"],
        )

        result = agent.provision_workspace(
            user_message="Create dev workspace for test team",
            auto_approve=True,
        )

        # Verify pipeline executed in order
        mock_components["intent"].recognize_intent.assert_called_once()
        mock_components["decision"].make_decision.assert_called_once()
        mock_components["generator"].generate.assert_called_once()
        mock_components["executor"].execute_deployment.assert_called_once()

        # Verify executor was called with correct parameters
        call_kwargs = mock_components["executor"].execute_deployment.call_args[1]
        assert call_kwargs["auto_approve"] is True
        assert call_kwargs["dry_run"] is False

        # Verify result
        assert result.success is True
        assert result.workspace_url == "https://adb-123.azuredatabricks.net"

    def test_successful_provision_dry_run(self, mock_components):
        """Test dry-run mode only executes plan."""
        mock_components["executor"].execute_deployment.return_value = DeploymentResult(
            success=True,
            workspace_url=None,
            workspace_id=None,
            resource_group_name=None,
            deployment_time_seconds=60.0,
            terraform_plan="Plan: 5 to add",
            terraform_outputs=None,
            error_message=None,
        )

        agent = InfrastructureAgent(
            intent_recognizer=mock_components["intent"],
            decision_engine=mock_components["decision"],
            terraform_generator=mock_components["generator"],
            terraform_executor=mock_components["executor"],
        )

        result = agent.provision_workspace(
            user_message="Create dev workspace",
            dry_run=True,
        )

        # Verify executor was called with dry_run=True
        call_kwargs = mock_components["executor"].execute_deployment.call_args[1]
        assert call_kwargs["dry_run"] is True

        # Verify result indicates dry-run
        assert result.success is True
        assert result.workspace_url is None
        assert result.terraform_plan is not None

    def test_provision_with_custom_working_dir(self, mock_components, tmp_path):
        """Test provisioning with custom working directory."""
        working_dir = tmp_path / "terraform"

        agent = InfrastructureAgent(
            intent_recognizer=mock_components["intent"],
            decision_engine=mock_components["decision"],
            terraform_generator=mock_components["generator"],
            terraform_executor=mock_components["executor"],
            working_dir=working_dir,
        )

        result = agent.provision_workspace(
            user_message="Create workspace",
            auto_approve=True,
        )

        # Verify executor was called with custom working_dir
        call_kwargs = mock_components["executor"].execute_deployment.call_args[1]
        assert call_kwargs["working_dir"] == working_dir

        assert result.success is True

    def test_provision_uses_temp_dir_by_default(self, mock_components):
        """Test that provisioning uses temporary directory by default."""
        agent = InfrastructureAgent(
            intent_recognizer=mock_components["intent"],
            decision_engine=mock_components["decision"],
            terraform_generator=mock_components["generator"],
            terraform_executor=mock_components["executor"],
        )

        result = agent.provision_workspace(
            user_message="Create workspace",
            auto_approve=True,
        )

        # Verify executor was called with a Path object (temp dir)
        call_kwargs = mock_components["executor"].execute_deployment.call_args[1]
        assert isinstance(call_kwargs["working_dir"], Path)

        assert result.success is True

    def test_provision_intent_recognizer_failure(self, mock_components):
        """Test handling of intent recognizer failure."""
        mock_components["intent"].recognize_intent.side_effect = Exception(
            "Failed to parse"
        )

        agent = InfrastructureAgent(
            intent_recognizer=mock_components["intent"],
            decision_engine=mock_components["decision"],
            terraform_generator=mock_components["generator"],
            terraform_executor=mock_components["executor"],
        )

        result = agent.provision_workspace(
            user_message="Invalid request",
            auto_approve=True,
        )

        # Should return failed result, not raise exception
        assert result.success is False
        assert result.error_message is not None
        assert "Failed to parse" in result.error_message

        # Should not call subsequent components
        mock_components["decision"].make_decision.assert_not_called()
        mock_components["generator"].generate.assert_not_called()
        mock_components["executor"].execute_deployment.assert_not_called()

    def test_provision_decision_engine_failure(self, mock_components):
        """Test handling of decision engine failure."""
        mock_components["decision"].make_decision.side_effect = Exception(
            "Decision failed"
        )

        agent = InfrastructureAgent(
            intent_recognizer=mock_components["intent"],
            decision_engine=mock_components["decision"],
            terraform_generator=mock_components["generator"],
            terraform_executor=mock_components["executor"],
        )

        result = agent.provision_workspace(
            user_message="Create workspace",
            auto_approve=True,
        )

        assert result.success is False
        assert "Decision failed" in result.error_message

        # Intent recognizer should be called, but not subsequent components
        mock_components["intent"].recognize_intent.assert_called_once()
        mock_components["generator"].generate.assert_not_called()
        mock_components["executor"].execute_deployment.assert_not_called()

    def test_provision_terraform_generator_failure(self, mock_components):
        """Test handling of Terraform generator failure."""
        mock_components["generator"].generate.side_effect = Exception("Generation failed")

        agent = InfrastructureAgent(
            intent_recognizer=mock_components["intent"],
            decision_engine=mock_components["decision"],
            terraform_generator=mock_components["generator"],
            terraform_executor=mock_components["executor"],
        )

        result = agent.provision_workspace(
            user_message="Create workspace",
            auto_approve=True,
        )

        assert result.success is False
        assert "Generation failed" in result.error_message

        # First two components should be called
        mock_components["intent"].recognize_intent.assert_called_once()
        mock_components["decision"].make_decision.assert_called_once()
        mock_components["executor"].execute_deployment.assert_not_called()

    def test_provision_terraform_executor_failure(self, mock_components):
        """Test handling of Terraform executor failure."""
        mock_components["executor"].execute_deployment.return_value = DeploymentResult(
            success=False,
            workspace_url=None,
            workspace_id=None,
            resource_group_name=None,
            deployment_time_seconds=30.0,
            terraform_plan=None,
            terraform_outputs=None,
            error_message="Terraform apply failed: resource conflict",
        )

        agent = InfrastructureAgent(
            intent_recognizer=mock_components["intent"],
            decision_engine=mock_components["decision"],
            terraform_generator=mock_components["generator"],
            terraform_executor=mock_components["executor"],
        )

        result = agent.provision_workspace(
            user_message="Create workspace",
            auto_approve=True,
        )

        # All components should be called
        mock_components["intent"].recognize_intent.assert_called_once()
        mock_components["decision"].make_decision.assert_called_once()
        mock_components["generator"].generate.assert_called_once()
        mock_components["executor"].execute_deployment.assert_called_once()

        # Result should indicate failure from executor
        assert result.success is False
        assert "resource conflict" in result.error_message

    def test_provision_tracks_total_time(self, mock_components):
        """Test that provisioning tracks total execution time."""
        agent = InfrastructureAgent(
            intent_recognizer=mock_components["intent"],
            decision_engine=mock_components["decision"],
            terraform_generator=mock_components["generator"],
            terraform_executor=mock_components["executor"],
        )

        result = agent.provision_workspace(
            user_message="Create workspace",
            auto_approve=True,
        )

        # Should have deployment time from executor
        assert result.deployment_time_seconds is not None
        assert result.deployment_time_seconds >= 0

    def test_destroy_workspace_success(self, mock_components, tmp_path):
        """Test successful workspace destruction."""
        mock_components["executor"].destroy_deployment.return_value = DeploymentResult(
            success=True,
            workspace_url=None,
            workspace_id=None,
            resource_group_name=None,
            deployment_time_seconds=60.0,
            terraform_plan=None,
            terraform_outputs=None,
            error_message=None,
        )

        agent = InfrastructureAgent(
            intent_recognizer=mock_components["intent"],
            decision_engine=mock_components["decision"],
            terraform_generator=mock_components["generator"],
            terraform_executor=mock_components["executor"],
        )

        result = agent.destroy_workspace(
            working_dir=tmp_path,
            auto_approve=True,
        )

        mock_components["executor"].destroy_deployment.assert_called_once_with(
            working_dir=tmp_path,
            auto_approve=True,
        )

        assert result.success is True

    def test_destroy_workspace_failure(self, mock_components, tmp_path):
        """Test handling of workspace destruction failure."""
        mock_components["executor"].destroy_deployment.return_value = DeploymentResult(
            success=False,
            workspace_url=None,
            workspace_id=None,
            resource_group_name=None,
            deployment_time_seconds=30.0,
            terraform_plan=None,
            terraform_outputs=None,
            error_message="Terraform destroy failed",
        )

        agent = InfrastructureAgent(
            intent_recognizer=mock_components["intent"],
            decision_engine=mock_components["decision"],
            terraform_generator=mock_components["generator"],
            terraform_executor=mock_components["executor"],
        )

        result = agent.destroy_workspace(
            working_dir=tmp_path,
            auto_approve=True,
        )

        assert result.success is False
        assert "Terraform destroy failed" in result.error_message

    def test_destroy_workspace_exception_handling(self, mock_components, tmp_path):
        """Test exception handling during workspace destruction."""
        mock_components["executor"].destroy_deployment.side_effect = Exception(
            "Unexpected error"
        )

        agent = InfrastructureAgent(
            intent_recognizer=mock_components["intent"],
            decision_engine=mock_components["decision"],
            terraform_generator=mock_components["generator"],
            terraform_executor=mock_components["executor"],
        )

        result = agent.destroy_workspace(
            working_dir=tmp_path,
            auto_approve=False,
        )

        assert result.success is False
        assert result.error_message is not None
        assert "Unexpected error" in result.error_message

    def test_provision_pipeline_data_flow(self, mock_components):
        """Test that data flows correctly through the pipeline."""
        agent = InfrastructureAgent(
            intent_recognizer=mock_components["intent"],
            decision_engine=mock_components["decision"],
            terraform_generator=mock_components["generator"],
            terraform_executor=mock_components["executor"],
        )

        result = agent.provision_workspace(
            user_message="Create prod workspace for ML team",
            auto_approve=True,
        )

        # Verify intent recognizer received user message
        assert mock_components["intent"].recognize_intent.call_args[0][0] == "Create prod workspace for ML team"

        # Verify decision engine received request from intent recognizer
        decision_input = mock_components["decision"].make_decision.call_args[0][0]
        assert isinstance(decision_input, InfrastructureRequest)

        # Verify generator received decision from decision engine
        generator_input = mock_components["generator"].generate.call_args[0][0]
        assert isinstance(generator_input, InfrastructureDecision)

        # Verify executor received files from generator
        executor_input = mock_components["executor"].execute_deployment.call_args[1]["terraform_files"]
        assert isinstance(executor_input, TerraformFiles)

        assert result.success is True
