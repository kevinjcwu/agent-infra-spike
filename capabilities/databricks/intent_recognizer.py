"""
Intent recognizer for parsing natural language infrastructure requests.

This module uses Azure OpenAI GPT-4 with function calling to parse user requests
into structured InfrastructureRequest objects.
"""

import json
import logging

from openai import AzureOpenAI

from agent.config import Config

from .models import InfrastructureRequest

logger = logging.getLogger(__name__)


class IntentRecognizer:
    """
    Parses natural language requests into structured infrastructure requests.

    Uses Azure OpenAI GPT-4 with function calling to extract structured data
    from user queries like "Create prod workspace for ML team in East US".
    """

    def __init__(
        self,
        azure_endpoint: str | None = None,
        api_key: str | None = None,
        api_version: str | None = None,
        deployment_name: str | None = None,
        temperature: float | None = None,
    ):
        """
        Initialize the intent recognizer with Azure OpenAI client.

        Args:
            azure_endpoint: Azure OpenAI endpoint URL (defaults to Config)
            api_key: Azure OpenAI API key (defaults to Config)
            api_version: Azure OpenAI API version (defaults to Config)
            deployment_name: Azure OpenAI deployment/model name (defaults to Config)
            temperature: Temperature for generation (defaults to Config)
        """
        self.azure_endpoint = azure_endpoint or Config.AZURE_OPENAI_ENDPOINT
        self.api_key = api_key or Config.AZURE_OPENAI_API_KEY
        self.api_version = api_version or Config.AZURE_OPENAI_API_VERSION
        self.deployment_name = deployment_name or Config.AZURE_OPENAI_DEPLOYMENT_NAME
        self.temperature = temperature or Config.AZURE_OPENAI_TEMPERATURE

        # Initialize Azure OpenAI client
        self.client = AzureOpenAI(
            azure_endpoint=self.azure_endpoint,
            api_key=self.api_key,
            api_version=self.api_version,
        )

        logger.info(
            f"IntentRecognizer initialized with deployment: {self.deployment_name}"
        )

    def recognize_intent(self, user_message: str) -> InfrastructureRequest:
        """
        Parse a natural language request into a structured InfrastructureRequest.

        Uses Azure OpenAI function calling to extract structured parameters from
        the user's message.

        Args:
            user_message: Natural language request from user

        Returns:
            InfrastructureRequest with parsed parameters

        Raises:
            ValueError: If the request cannot be parsed or is invalid

        Examples:
            >>> recognizer = IntentRecognizer()
            >>> request = recognizer.recognize_intent(
            ...     "Create prod workspace for ML team in East US with GPU"
            ... )
            >>> request.environment
            'prod'
            >>> request.enable_gpu
            True
        """
        logger.info(f"Parsing user request: {user_message}")

        try:
            # Define the tool schema for structured output (OpenAI SDK v1.0+)
            tools = [
                {
                    "type": "function",
                    "function": {
                        "name": "create_infrastructure_request",
                        "description": "Extract infrastructure provisioning parameters from user request",
                        "parameters": {
                            "type": "object",
                            "properties": {
                                "workspace_name": {
                                    "type": "string",
                                    "description": "Name for the Databricks workspace. If not specified, generate from team and environment.",
                                },
                                "team": {
                                    "type": "string",
                                    "description": "Team name (e.g., 'data_science', 'ml', 'data_engineering', 'analytics')",
                                },
                                "environment": {
                                    "type": "string",
                                    "enum": ["dev", "staging", "prod"],
                                    "description": "Deployment environment",
                                },
                                "region": {
                                    "type": "string",
                                    "description": "Azure region (e.g., 'eastus', 'westus2', 'centralus')",
                                },
                                "enable_gpu": {
                                    "type": "boolean",
                                    "description": "Whether GPU instances are required (true for ML/training workloads)",
                                },
                                "workload_type": {
                                    "type": "string",
                                    "enum": [
                                        "data_engineering",
                                        "ml",
                                        "analytics",
                                        "data_science",
                                        "etl",
                                    ],
                                    "description": "Type of workload this workspace will handle",
                                },
                                "cost_limit": {
                                    "type": "number",
                                    "description": "Optional monthly cost limit in USD",
                                },
                                "additional_requirements": {
                                    "type": "string",
                                    "description": "Any additional requirements or notes from the user",
                                },
                            },
                            "required": ["team", "environment", "region"],
                        },
                    },
                }
            ]

            # Create system prompt to guide the model
            system_prompt = """You are an infrastructure provisioning assistant that extracts structured parameters from user requests.

Your task is to parse natural language requests for Databricks workspace provisioning and extract:
- Team name and environment (dev/staging/prod)
- Azure region
- Whether GPU support is needed (look for keywords: ML, machine learning, training, GPU, deep learning)
- Workload type (data_engineering, ml, analytics, data_science, etl)
- Any cost constraints
- Workspace name (if not specified, suggest one based on team and environment)

Guidelines:
- If GPU is mentioned or it's an ML/training workload, set enable_gpu=true
- Default workload_type to 'ml' if GPU is needed, otherwise 'data_engineering'
- Normalize region names to Azure format (e.g., "East US" → "eastus")
- If workspace name is not specified, generate as "{team}-{environment}"
- Be conservative with cost limits - only set if explicitly mentioned
"""

            # Call Azure OpenAI with tool calling
            response = self.client.chat.completions.create(
                model=self.deployment_name,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_message},
                ],
                tools=tools,  # type: ignore[arg-type]
                tool_choice={"type": "function", "function": {"name": "create_infrastructure_request"}},  # type: ignore[arg-type]
                temperature=self.temperature,
            )

            # Extract tool call arguments
            message = response.choices[0].message

            if not message.tool_calls or len(message.tool_calls) == 0:
                raise ValueError(
                    "Azure OpenAI did not return a tool call. "
                    "This may indicate an issue with the request format."
                )

            # Parse the arguments from the first tool call
            tool_call = message.tool_calls[0]
            function_args = json.loads(tool_call.function.arguments)  # type: ignore[union-attr]
            logger.info(f"Extracted parameters: {function_args}")

            # Generate workspace name if not provided
            if "workspace_name" not in function_args or not function_args["workspace_name"]:
                team = function_args.get("team", "unknown").lower().replace(" ", "-")
                env = function_args.get("environment", "dev")
                function_args["workspace_name"] = f"{team}-{env}"
                logger.info(f"Generated workspace name: {function_args['workspace_name']}")

            # Set defaults for optional fields
            function_args.setdefault("enable_gpu", False)
            function_args.setdefault("workload_type", "data_engineering")

            # Normalize region to Azure format
            if "region" in function_args:
                function_args["region"] = self._normalize_region(function_args["region"])

            # Create and validate the request
            request = InfrastructureRequest(**function_args)
            logger.info(f"Successfully created InfrastructureRequest: {request.workspace_name}")

            return request

        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse function call arguments: {e}")
            raise ValueError(f"Invalid JSON in Azure OpenAI response: {e}") from e
        except Exception as e:
            logger.error(f"Error parsing intent: {e}")
            raise ValueError(f"Failed to parse infrastructure request: {e}") from e

    def _normalize_region(self, region: str) -> str:
        """
        Normalize region name to Azure format.

        Args:
            region: Region name (e.g., "East US", "eastus", "east-us")

        Returns:
            Normalized region name in Azure format (e.g., "eastus")

        Examples:
            >>> recognizer = IntentRecognizer()
            >>> recognizer._normalize_region("East US")
            'eastus'
            >>> recognizer._normalize_region("west-us-2")
            'westus2'
        """
        # Convert to lowercase and remove spaces/hyphens
        normalized = region.lower().replace(" ", "").replace("-", "")

        # Map common variations to Azure region names
        region_map = {
            "eastus": "eastus",
            "eastus2": "eastus2",
            "westus": "westus",
            "westus2": "westus2",
            "westus3": "westus3",
            "centralus": "centralus",
            "northcentralus": "northcentralus",
            "southcentralus": "southcentralus",
            "westcentralus": "westcentralus",
        }

        return region_map.get(normalized, normalized)
