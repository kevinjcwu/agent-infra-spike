"""
Infrastructure Orchestrator using Microsoft Agent Framework.

Provides conversational interface for infrastructure provisioning.
"""

import os
from typing import Any

from agent_framework.azure import AzureOpenAIChatClient
from dotenv import load_dotenv

import orchestrator.tools  # noqa: F401 - Import for tool registration side effects
from capabilities import BaseCapability, CapabilityContext
from capabilities.databricks import DatabricksCapability
from orchestrator.capability_registry import capability_registry
from orchestrator.models import ConversationState, ProvisioningPlan
from orchestrator.tool_manager import tool_manager

# Load environment variables
load_dotenv(override=True)


class InfrastructureOrchestrator:
    """
    MAF-based orchestrator for infrastructure provisioning.

    Responsibilities:
    - Engage in multi-turn conversations to gather requirements
    - Ask clarifying questions (RG name, budget, constraints)
    - Suggest smart naming defaults
    - Discover required capabilities
    - Generate and validate provisioning plans
    - Obtain user approval before execution
    """

    def __init__(self):
        """Initialize the orchestrator with MAF agent."""
        self.agent = self._create_agent()
        self.state = ConversationState()
        self.current_plan: ProvisioningPlan | None = None
        self.capabilities: dict[str, BaseCapability] = {}
        self._register_capabilities()
        # Create a persistent thread for conversation history
        # According to MAF docs: call get_new_thread() to create persistent thread
        # If we don't create thread explicitly, each run gets a "throwaway thread"
        self.thread = self.agent.get_new_thread()

    def _register_capabilities(self):
        """Register all available capabilities.

        Capabilities are loaded here to make them available for execution.
        To add a new capability, simply instantiate it and add to the dict.
        """
        # Register Databricks capability
        self.capabilities["provision_databricks"] = DatabricksCapability()

        # Future capabilities:
        # self.capabilities["provision_openai"] = OpenAICapability()
        # self.capabilities["configure_firewall"] = FirewallCapability()

    def _create_agent(self):
        """Create MAF agent with tools and system prompt."""
        # Get Azure OpenAI configuration from environment
        endpoint = os.environ.get("AZURE_OPENAI_ENDPOINT")
        deployment = os.environ.get("AZURE_OPENAI_DEPLOYMENT_NAME")
        api_key = os.environ.get("AZURE_OPENAI_API_KEY")
        api_version = os.environ.get("AZURE_OPENAI_API_VERSION", "2025-03-01-preview")

        if not all([endpoint, deployment, api_key]):
            raise ValueError(
                "Missing Azure OpenAI configuration. "
                "Set AZURE_OPENAI_ENDPOINT, AZURE_OPENAI_DEPLOYMENT_NAME, and AZURE_OPENAI_API_KEY"
            )

        # Create client and agent
        client = AzureOpenAIChatClient(
            endpoint=endpoint,
            deployment_name=deployment,
            api_key=api_key,
            api_version=api_version,
        )

        # Get actual tool functions (not schemas) - MAF handles tool calling automatically
        tool_functions = tool_manager.get_tool_functions()

        print(f"[DEBUG] Registering {len(tool_functions)} tools with MAF:")
        for func in tool_functions:
            print(f"  - {func.__name__}")

        return client.create_agent(
            name="InfrastructureOrchestrator",
            instructions=self._get_system_prompt(),
            # Pass actual Python functions - MAF auto-generates schemas and handles calling
            tools=tool_functions,
        )

    def _get_system_prompt(self) -> str:
        """Get the system prompt that defines orchestrator behavior."""
        # Get available capabilities from registry
        capabilities_desc = capability_registry.get_capabilities_description()

        return f"""You are an expert infrastructure provisioning orchestrator for Azure and Databricks.

**Your Role**:
Help users provision cloud infrastructure through natural conversation. Guide them step-by-step,
gathering all required information before proposing a deployment plan.

**Available Infrastructure Capabilities**:

{capabilities_desc}

**IMPORTANT - Capability Selection**:
When you understand what infrastructure the user needs, call the `select_capabilities` tool with:
- Exact capability names from the list above (e.g., "provision_databricks")
- A clear rationale explaining why these capabilities were selected

You MUST use exact capability names. The tool will validate and reject unknown capabilities.

**Your Process** (FOLLOW THIS ORDER):
1. **Understand Intent**: Listen to what the user needs (e.g., "I need Databricks")
2. **IMMEDIATELY call select_capabilities**: As soon as you know what they want,
   call `select_capabilities` with exact capability names. Do this FIRST, before asking questions.
3. **Track what you already know**: Remember ALL information the user has provided:
   - Initial request (what capability they need)
   - Team name
   - Environment (dev/staging/prod)
   - Region
   - Workload type (data_engineering, ml, analytics)
   - GPU requirements (yes/no)
4. **Ask for missing info only**: Only ask for information you DON'T already have.
   If user provides multiple details at once, extract and remember ALL of them.
5. **Once you have all required info**:
   - Call `suggest_naming` to generate resource names
   - Call `estimate_cost` to calculate monthly costs
   - Present complete plan with all details
6. **Get Approval**: Ask user to confirm the plan
7. **When user approves** (says "yes", "go ahead", "proceed", "deploy", etc.):
   - IMMEDIATELY call `execute_deployment` tool with all parameters
   - DO NOT just say you'll deploy - ACTUALLY CALL THE TOOL

CRITICAL:
- ALWAYS call `select_capabilities` first when you understand what infrastructure is needed
- REMEMBER context from earlier in the conversation
- If user provides multiple details in one message, extract ALL of them
- Don't ask for info they already gave you
- When user approves deployment, you MUST call execute_deployment - do not just acknowledge

**Communication Style**:
- Conversational and helpful (not robotic)
- Ask ONE question at a time (don't overwhelm)
- Provide context for your suggestions
- Explain trade-offs when relevant
- Be proactive with defaults but allow overrides

**Example Flow**:
User: "I need Databricks for ML experimentation"
You think: User needs Databricks for ML
You call: select_capabilities(capabilities=["provision_databricks"], rationale="User needs ML workspace")
You say: "Great! I'll help set up Databricks for ML. I need a few details:
- Team name?
- Environment (dev/staging/prod)?
- Azure region?
- GPU support needed?"

User: "team: e2e-test, env: dev, region: eastus, GPU: no"
You think: User provided team=e2e-test, environment=dev, region=eastus, GPU=no. I have everything!
You call: suggest_naming(team="e2e-test", environment="dev", resource_type="workspace")
You call: estimate_cost(capability="provision_databricks", configuration={...})
You say: "Perfect! Here's the plan:
- Resource Group: rg-e2e-test-dev
- Workspace: e2e-test-dev
- Estimated cost: $200/month
Shall I proceed?"

User: "yes, go ahead"
You think: User approved! Must call execute_deployment now.
You call: execute_deployment(capability_name="provision_databricks", user_request="...", parameters={...})
You say: [Agent will see deployment results and share them with user]

**Tools Available**:
- `select_capabilities`: Declare which capabilities are needed (MUST use exact names)
- `suggest_naming`: Generate Azure-compliant naming suggestions
- `estimate_cost`: Calculate monthly cost estimates
- `execute_deployment`: Deploy infrastructure after user approves plan

**Important**:
- Always use exact capability names from the list when calling select_capabilities
- Suggest smart defaults (don't make users think from scratch)
- Explain WHY you suggest something (e.g., "East US recommended for ML due to GPU availability")
- Get explicit approval before calling execute_deployment
- After user approves, call execute_deployment with: capability_name, user_request, and all gathered parameters
"""

    async def process_message(self, user_message: str) -> str:
        """
        Process a user message and return orchestrator response.

        The MAF agent handles conversation history automatically,
        so we just pass messages and extract responses.

        MAF tool calling pattern:
        1. agent.run() returns response (may include tool_calls)
        2. We execute tools and send results back
        3. agent.run() again with tool results to get final response

        Args:
            user_message: User's message

        Returns:
            Orchestrator's response
        """
        # Update state
        self.state.messages_count += 1

        # Process with MAF agent - pass thread to maintain conversation history
        # MAF automatically handles tool calling when we pass function tools
        response = await self.agent.run(user_message, thread=self.thread)

        # Update thread from response (MAF updates it with conversation history)
        if hasattr(response, 'thread') and response.thread:
            self.thread = response.thread

        # Check if execute_deployment tool was called
        # If so, actually execute the deployment
        deployment_triggered = False
        if hasattr(response, 'messages') and response.messages:
            for msg in response.messages:
                # Check for function call messages
                if hasattr(msg, 'contents'):
                    for content in msg.contents:
                        # Look for FunctionCallContent with name 'execute_deployment'
                        if hasattr(content, 'name') and content.name == 'execute_deployment':
                            # Extract parameters from the function call
                            if hasattr(content, 'arguments'):
                                import json
                                args = json.loads(content.arguments) if isinstance(content.arguments, str) else content.arguments

                                print(f"\n🚀 [DEPLOYMENT TRIGGERED] Executing {args.get('capability_name')}...")
                                print(f"[DEBUG] Function call args: {args}")

                                try:
                                    # Extract parameters from tool call
                                    parameters = {
                                        'team': args.get('team'),
                                        'environment': args.get('environment'),
                                        'region': args.get('region'),
                                        'workspace_name': args.get('workspace_name'),
                                        'enable_gpu': args.get('enable_gpu', False),
                                        'workload_type': args.get('workload_type', 'ml'),
                                    }

                                    print(f"[DEBUG] Deployment parameters: {parameters}")

                                    # Actually execute the capability
                                    plan, result = await self.execute_capability(
                                        capability_name=args.get('capability_name', 'provision_databricks'),
                                        user_request='Deploy infrastructure',
                                        parameters=parameters
                                    )

                                    # Update state
                                    self.state.plan_approved = True
                                    self.state.deployment_complete = True
                                    deployment_triggered = True

                                    print(f"\n✅ [DEPLOYMENT COMPLETE] {result.message}")

                                except Exception as e:
                                    print(f"\n❌ [DEPLOYMENT FAILED] {e}")
                                    import traceback
                                    traceback.print_exc()

        # Extract text response
        response_text = response.text if hasattr(response, 'text') else str(response)

        # If deployment was triggered, append a note about checking the output above
        if deployment_triggered:
            response_text += "\n\n(See deployment results above)"

        return response_text

    async def start_conversation(self, initial_message: str | None = None) -> str:
        """
        Start a new infrastructure provisioning conversation.

        Args:
            initial_message: Optional initial message from user

        Returns:
            Orchestrator's greeting or response
        """
        if initial_message:
            return await self.process_message(initial_message)

        # Default greeting
        return await self.process_message(
            "Hello! I'd like to provision some infrastructure. Can you help?"
        )

    def get_state(self) -> ConversationState:
        """Get current conversation state."""
        return self.state

    async def execute_capability(
        self,
        capability_name: str,
        user_request: str,
        parameters: dict[str, Any]
    ):
        """Execute a capability after gathering requirements.

        This method:
        1. Creates capability context from conversation parameters
        2. Generates execution plan
        3. Presents plan to user for approval
        4. Executes if approved

        Args:
            capability_name: Name of capability to execute (e.g., 'provision_databricks')
            user_request: Original user request
            parameters: Parameters gathered during conversation

        Returns:
            Tuple of (plan, result) where result is None if not approved/executed

        Raises:
            ValueError: If capability not found or validation fails
        """
        # Validate capability exists
        if capability_name not in self.capabilities:
            raise ValueError(
                f"Unknown capability '{capability_name}'. "
                f"Available: {list(self.capabilities.keys())}"
            )

        capability = self.capabilities[capability_name]

        # Create context
        context = CapabilityContext(
            user_request=user_request,
            capability_name=capability_name,
            parameters=parameters,
            metadata={
                "orchestrator": "InfrastructureOrchestrator",
                "conversation_messages": self.state.messages_count,
            }
        )

        # Validate context
        is_valid, errors = await capability.validate(context)
        if not is_valid:
            raise ValueError(f"Capability validation failed: {', '.join(errors)}")

        # Generate plan
        print(f"\n🔍 Generating plan for {capability_name}...")
        plan = await capability.plan(context)

        # Store plan in state (convert capability plan to orchestrator plan)
        self.current_plan = ProvisioningPlan(
            capability=capability_name,
            workspace_name=parameters.get("workspace_name", ""),
            resource_group=parameters.get("resource_group", ""),
            region=parameters.get("region", "eastus"),
            team=parameters.get("team", ""),
            environment=parameters.get("environment", "dev"),
            enable_gpu=parameters.get("enable_gpu", False),
            workload_type=parameters.get("workload_type", "data_engineering"),
            estimated_cost=plan.estimated_cost or 0.0,
            requires_approval=plan.requires_approval,
        )
        self.state.plan_proposed = True

        # Present plan to user
        print("\n" + "="*80)
        print("📋 EXECUTION PLAN")
        print("="*80)
        print(plan.to_summary())
        print("="*80)

        # Note: In Phase 2, we're adding the plumbing but not the full approval flow
        # For now, we'll execute directly. Phase 4 will add approval workflow.
        if plan.requires_approval:
            print("\n⚠️  This plan requires approval before execution.")
            print("(Phase 4 will add interactive approval workflow)")
            print("For now, auto-approving for testing...\n")

        self.state.plan_approved = True

        # Execute
        print(f"🚀 Executing {capability_name}...")
        result = await capability.execute(plan)

        # Display result
        print("\n" + "="*80)
        print("📊 EXECUTION RESULT")
        print("="*80)
        print(result.to_summary())
        print("="*80 + "\n")

        return plan, result

    def get_capability(self, name: str) -> BaseCapability | None:
        """Get a registered capability by name.

        Args:
            name: Capability name

        Returns:
            Capability instance or None if not found
        """
        return self.capabilities.get(name)

    def list_capabilities(self) -> list[str]:
        """Get list of all registered capability names.

        Returns:
            List of capability names
        """
        return list(self.capabilities.keys())

    def reset(self) -> None:
        """Reset the orchestrator state for a new conversation."""
        self.state = ConversationState()
        self.current_plan = None
        self.thread = self.agent.get_new_thread()  # Create new conversation thread
        print("[INFO] Orchestrator state reset")
