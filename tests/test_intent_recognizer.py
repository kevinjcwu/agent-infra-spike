"""
Tests for the intent recognizer.

Tests the IntentRecognizer's ability to parse natural language requests
into structured InfrastructureRequest objects. Uses mocked Azure OpenAI responses.
"""

from unittest.mock import Mock, patch

import pytest

from agent.intent_recognizer import IntentRecognizer
from agent.models import InfrastructureRequest


class TestIntentRecognizer:
    """Tests for IntentRecognizer class."""

    @pytest.fixture
    def mock_azure_client(self):
        """Create a mock Azure OpenAI client."""
        with patch("agent.intent_recognizer.AzureOpenAI") as mock_client:
            yield mock_client

    def _create_mock_response(self, function_args: dict) -> Mock:
        """
        Create a mock Azure OpenAI response with tool call.

        Args:
            function_args: Arguments to return in the function call

        Returns:
            Mock response object
        """
        import json

        mock_tool_call = Mock()
        mock_tool_call.function.arguments = json.dumps(function_args)

        mock_message = Mock()
        mock_message.tool_calls = [mock_tool_call]

        mock_choice = Mock()
        mock_choice.message = mock_message

        mock_response = Mock()
        mock_response.choices = [mock_choice]

        return mock_response

    def test_basic_request_parsing(self, mock_azure_client):
        """Test parsing a basic infrastructure request."""
        # Setup mock response
        mock_instance = mock_azure_client.return_value
        mock_instance.chat.completions.create.return_value = self._create_mock_response(
            {
                "team": "data_engineering",
                "environment": "dev",
                "region": "eastus",
            }
        )

        recognizer = IntentRecognizer()
        request = recognizer.recognize_intent("Create a dev workspace for data engineering team in East US")

        assert isinstance(request, InfrastructureRequest)
        assert request.team == "data_engineering"
        assert request.environment == "dev"
        assert request.region == "eastus"

    def test_ml_workspace_with_gpu(self, mock_azure_client):
        """Test parsing ML workspace request with GPU."""
        mock_instance = mock_azure_client.return_value
        mock_instance.chat.completions.create.return_value = self._create_mock_response(
            {
                "team": "ml",
                "environment": "prod",
                "region": "eastus",
                "enable_gpu": True,
                "workload_type": "ml",
            }
        )

        recognizer = IntentRecognizer()
        request = recognizer.recognize_intent(
            "Create prod workspace for ML team in East US with GPU support"
        )

        assert request.team == "ml"
        assert request.environment == "prod"
        assert request.enable_gpu is True
        assert request.workload_type == "ml"

    def test_workspace_name_generation(self, mock_azure_client):
        """Test automatic workspace name generation."""
        mock_instance = mock_azure_client.return_value
        mock_instance.chat.completions.create.return_value = self._create_mock_response(
            {
                "team": "data science",
                "environment": "staging",
                "region": "westus2",
            }
        )

        recognizer = IntentRecognizer()
        request = recognizer.recognize_intent("Create staging workspace for data science team")

        # Should generate name from team and environment
        assert "data" in request.workspace_name.lower()
        assert "staging" in request.workspace_name

    def test_region_normalization(self, mock_azure_client):
        """Test that region names are normalized."""
        mock_instance = mock_azure_client.return_value
        mock_instance.chat.completions.create.return_value = self._create_mock_response(
            {
                "team": "analytics",
                "environment": "dev",
                "region": "East US 2",  # Should be normalized
            }
        )

        recognizer = IntentRecognizer()
        request = recognizer.recognize_intent("Create workspace in East US 2")

        assert request.region == "eastus2"

    def test_cost_limit_parsing(self, mock_azure_client):
        """Test parsing cost limit from request."""
        mock_instance = mock_azure_client.return_value
        mock_instance.chat.completions.create.return_value = self._create_mock_response(
            {
                "team": "team",
                "environment": "dev",
                "region": "eastus",
                "cost_limit": 1000.0,
            }
        )

        recognizer = IntentRecognizer()
        request = recognizer.recognize_intent(
            "Create workspace with $1000/month budget limit"
        )

        assert request.cost_limit == 1000.0

    def test_additional_requirements(self, mock_azure_client):
        """Test parsing additional requirements."""
        mock_instance = mock_azure_client.return_value
        mock_instance.chat.completions.create.return_value = self._create_mock_response(
            {
                "team": "team",
                "environment": "prod",
                "region": "eastus",
                "additional_requirements": "Need VNet integration and private endpoints",
            }
        )

        recognizer = IntentRecognizer()
        request = recognizer.recognize_intent(
            "Create prod workspace with VNet integration and private endpoints"
        )

        assert "VNet" in request.additional_requirements
        assert "private endpoints" in request.additional_requirements

    def test_error_handling_no_tool_call(self, mock_azure_client):
        """Test error handling when Azure OpenAI doesn't return a tool call."""
        mock_instance = mock_azure_client.return_value

        mock_message = Mock()
        mock_message.tool_calls = None  # No tool calls

        mock_choice = Mock()
        mock_choice.message = mock_message

        mock_response = Mock()
        mock_response.choices = [mock_choice]

        mock_instance.chat.completions.create.return_value = mock_response

        recognizer = IntentRecognizer()

        with pytest.raises(ValueError, match="did not return a tool call"):
            recognizer.recognize_intent("Invalid request")

    def test_error_handling_invalid_json(self, mock_azure_client):
        """Test error handling when tool call has invalid JSON."""
        mock_instance = mock_azure_client.return_value

        mock_tool_call = Mock()
        mock_tool_call.function.arguments = "invalid json {{"

        mock_message = Mock()
        mock_message.tool_calls = [mock_tool_call]

        mock_choice = Mock()
        mock_choice.message = mock_message

        mock_response = Mock()
        mock_response.choices = [mock_choice]

        mock_instance.chat.completions.create.return_value = mock_response

        recognizer = IntentRecognizer()

        with pytest.raises(ValueError, match="Invalid JSON"):
            recognizer.recognize_intent("Some request")

    def test_default_values(self, mock_azure_client):
        """Test that default values are set for optional fields."""
        mock_instance = mock_azure_client.return_value
        mock_instance.chat.completions.create.return_value = self._create_mock_response(
            {
                "team": "team",
                "environment": "dev",
                "region": "eastus",
                # No enable_gpu or workload_type provided
            }
        )

        recognizer = IntentRecognizer()
        request = recognizer.recognize_intent("Create a workspace")

        assert request.enable_gpu is False  # Default
        assert request.workload_type == "data_engineering"  # Default

    def test_custom_client_configuration(self):
        """Test initializing with custom Azure OpenAI configuration."""
        with patch("agent.intent_recognizer.AzureOpenAI"):
            recognizer = IntentRecognizer(
                azure_endpoint="https://custom.openai.azure.com/",
                api_key="custom-key",
                api_version="2024-01-01",
                deployment_name="gpt-4-turbo",
                temperature=0.5,
            )

            assert recognizer.azure_endpoint == "https://custom.openai.azure.com/"
            assert recognizer.api_key == "custom-key"
            assert recognizer.api_version == "2024-01-01"
            assert recognizer.deployment_name == "gpt-4-turbo"
            assert recognizer.temperature == 0.5

    def test_region_normalization_variants(self):
        """Test various region name format normalizations."""
        recognizer = IntentRecognizer()

        test_cases = [
            ("East US", "eastus"),
            ("east-us", "eastus"),
            ("EASTUS", "eastus"),
            ("West US 2", "westus2"),
            ("west-us-2", "westus2"),
            ("Central US", "centralus"),
        ]

        for input_region, expected in test_cases:
            normalized = recognizer._normalize_region(input_region)
            assert normalized == expected, f"Failed for {input_region}"

    def test_explicit_workspace_name(self, mock_azure_client):
        """Test that explicit workspace names are preserved."""
        mock_instance = mock_azure_client.return_value
        mock_instance.chat.completions.create.return_value = self._create_mock_response(
            {
                "workspace_name": "my-custom-workspace",
                "team": "team",
                "environment": "dev",
                "region": "eastus",
            }
        )

        recognizer = IntentRecognizer()
        request = recognizer.recognize_intent(
            "Create workspace named my-custom-workspace"
        )

        assert request.workspace_name == "my-custom-workspace"
