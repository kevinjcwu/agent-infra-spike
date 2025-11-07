# Microsoft Agent Framework (MAF) Research & Implementation Plan

**Date**: November 6, 2025
**Purpose**: Deep dive into MAF for orchestrator implementation
**Status**: Research Complete → Ready for Phase-by-Phase Implementation

---

## 1. Microsoft Agent Framework Overview

### What is MAF?

Microsoft Agent Framework is a **comprehensive multi-language framework** (Python + .NET) for building, orchestrating, and deploying AI agents with support for:

- **Simple chat agents** (single-turn interactions)
- **Complex multi-agent workflows** (graph-based orchestration)
- **Human-in-the-loop approvals**
- **State management and checkpointing**
- **Built-in observability** (OpenTelemetry)

### Key Components

```
┌──────────────────────────────────────────────────────────────┐
│                    MICROSOFT AGENT FRAMEWORK                  │
├──────────────────────────────────────────────────────────────┤
│                                                               │
│  ┌─────────────┐  ┌──────────────┐  ┌──────────────────┐   │
│  │   Agents    │  │  Workflows   │  │  Chat Clients    │   │
│  │             │  │              │  │                  │   │
│  │ - Basic     │  │ - Graph-     │  │ - Azure OpenAI   │   │
│  │ - Tool use  │  │   based      │  │ - OpenAI         │   │
│  │ - Streaming │  │ - Streaming  │  │ - Other LLMs     │   │
│  │ - Memory    │  │ - Checkpoint │  │                  │   │
│  └─────────────┘  └──────────────┘  └──────────────────┘   │
│                                                               │
│  ┌─────────────┐  ┌──────────────┐  ┌──────────────────┐   │
│  │ Middleware  │  │ Observability│  │  DevUI           │   │
│  │             │  │              │  │                  │   │
│  │ - Request/  │  │ - OpenTeleme-│  │ - Interactive    │   │
│  │   Response  │  │   try        │  │   testing        │   │
│  │ - Exception │  │ - Monitoring │  │ - Debugging      │   │
│  │   handling  │  │ - Tracing    │  │ - Visualization  │   │
│  └─────────────┘  └──────────────┘  └──────────────────┘   │
│                                                               │
└──────────────────────────────────────────────────────────────┘
```

---

## 2. Core Concepts for Our Implementation

### 2.1 Agents

**Definition**: An agent in MAF is a unit that can:
- Process user input
- Use tools/functions
- Maintain conversation context
- Generate responses using LLMs

**Basic Pattern** (Python):
```python
from agent_framework.azure import AzureOpenAIResponsesClient
from azure.identity import AzureCliCredential

async def create_agent():
    agent = AzureOpenAIResponsesClient(
        credential=AzureCliCredential(),
    ).create_agent(
        name="InfrastructureOrchestrator",
        instructions="You are an infrastructure provisioning orchestrator...",
    )

    response = await agent.run("Create a Databricks workspace")
    return response
```

**Key Features for Us:**
- ✅ **Multi-turn conversations** (maintain context across messages)
- ✅ **Tool calling** (can invoke capabilities)
- ✅ **Structured output** (return JSON/typed objects)
- ✅ **Memory/state** (remember previous interactions)

### 2.2 Workflows

**Definition**: Workflows orchestrate multiple agents and functions in a graph-based pattern with:
- **Data flow connections** between nodes
- **Streaming support** for real-time updates
- **Checkpointing** for state persistence
- **Human-in-the-loop** approval gates
- **Time-travel** debugging

**Workflow Pattern**:
```python
from agent_framework.workflows import Workflow, WorkflowNode

class InfrastructureOrchestrationWorkflow(Workflow):
    """
    Orchestrates multi-capability infrastructure provisioning
    """

    async def run(self, user_request: str):
        # Step 1: Analyze intent (LLM-based)
        intent = await self.analyze_intent_node(user_request)

        # Step 2: Determine capabilities (LLM-based)
        capabilities = await self.capability_discovery_node(intent)

        # Step 3: User validation (human-in-the-loop)
        validated = await self.user_validation_node(capabilities)

        # Step 4: Execute capabilities (deterministic routing)
        results = await self.execute_capabilities_node(validated)

        return results
```

**Why Workflows Matter for Us:**
- Our orchestrator needs to route between multiple capabilities
- We need human approval at various stages
- State management across multi-step processes
- Ability to checkpoint and resume after failures

### 2.3 Chat Clients vs Agents

**Chat Client**: Direct LLM interaction (like we currently use with OpenAI API)
```python
# Current approach (direct OpenAI)
from openai import AzureOpenAI

client = AzureOpenAI(...)
response = client.chat.completions.create(...)
```

**Agent**: Wrapper around chat client with additional capabilities
```python
# MAF approach (agent with tools)
agent = chat_client.create_agent(
    name="Orchestrator",
    tools=[capability_router, user_validator, ...],
)
response = await agent.run("Deploy infrastructure")
# Agent can call tools, maintain context, etc.
```

**For Our Use Case:**
- **Orchestrator = Agent** (needs tools, context, multi-turn)
- **Capabilities = Can be Agents OR Workflows** depending on complexity
- **Simple operations = Chat Client** (no agent overhead)

---

## 3. Architecture Mapping to MAF Concepts

### Current Spike Architecture
```
CLI → InfrastructureAgent → IntentRecognizer → DecisionEngine → TerraformGenerator → TerraformExecutor
     (orchestrator)         (OpenAI function)   (Python logic)   (Jinja2)           (subprocess)
```

### Target MAF Architecture
```
CLI → OrchestratorAgent (MAF Agent with workflow)
        │
        ├─→ Capability Discovery (Agent tool)
        ├─→ User Validation (Human-in-loop workflow node)
        └─→ Capability Execution (Workflow routing)
              │
              ├─→ DatabricksCapability (Sub-workflow/Agent)
              │     ├─→ IntentRecognizer (Workflow node)
              │     ├─→ DecisionEngine (Workflow node)
              │     ├─→ TerraformGenerator (Workflow node)
              │     └─→ TerraformExecutor (Workflow node)
              │
              ├─→ OpenAICapability (Future)
              └─→ FirewallCapability (Future)
```

### Key MAF Components We'll Use

| MAF Component | Our Usage | Why |
|---------------|-----------|-----|
| **Agent** | Orchestrator | Multi-turn conversation, tool calling |
| **Workflow** | Capability execution flows | Graph-based orchestration, checkpointing |
| **Tools/Functions** | Capability registry, validators | Agent can invoke capabilities dynamically |
| **Human-in-the-loop** | Approval gates | User validation at critical steps |
| **State Management** | MAF built-in conversation context | Conversation history automatic; only store final plan data |
| **Middleware** | Error handling, logging | Centralized request/response processing |

---

## 4. Implementation Plan (Phase by Phase)

### Phase 0: Environment Setup (Day 0)
**Goal**: Install MAF and validate basic functionality

**Tasks**:
```bash
# 1. Install MAF
pip install agent-framework --pre

# 2. Verify installation
python -c "from agent_framework import __version__; print(__version__)"

# 3. Create simple test agent
# (see code below)

# 4. Test Azure OpenAI connectivity
# (validate existing credentials work with MAF)
```

**Test Script** (`tests/test_maf_setup.py`):
```python
import asyncio
from agent_framework.azure import AzureOpenAIResponsesClient
from azure.identity import AzureCliCredential

async def test_basic_agent():
    """Verify MAF works with our Azure OpenAI setup"""
    agent = AzureOpenAIResponsesClient(
        credential=AzureCliCredential(),
    ).create_agent(
        name="TestBot",
        instructions="You are a helpful assistant.",
    )

    response = await agent.run("Say hello!")
    print(f"✓ Agent responded: {response}")
    assert "hello" in response.lower()

if __name__ == "__main__":
    asyncio.run(test_basic_agent())
```

**Success Criteria**:
- ✅ MAF installed without errors
- ✅ Test agent can communicate with Azure OpenAI
- ✅ Basic conversation works

**Estimated Time**: 1-2 hours

---

### Phase 1: Conversational Orchestrator (Days 1-3)
**Goal**: Build MAF-based orchestrator with multi-turn conversation

**Structure**:
```
orchestrator/
├── __init__.py
├── orchestrator_agent.py         # Main MAF agent
├── tools.py                      # Agent tools (capability discovery, etc.)
└── models.py                     # Orchestrator data models
```

**Note**: No separate `conversation_manager.py` needed - MAF agents handle conversation state natively!

**Key Code** (`orchestrator/orchestrator_agent.py`):
```python
from agent_framework.azure import AzureOpenAIResponsesClient
from azure.identity import AzureCliCredential
from typing import Optional
import json

class InfrastructureOrchestrator:
    """
    MAF-based orchestrator for infrastructure provisioning.

    Responsibilities:
    1. Understand user intent through multi-turn conversation
    2. Ask clarifying questions (RG name, budget, constraints)
    3. Discover required capabilities
    4. Validate plan with user
    5. Execute capabilities
    """

    def __init__(self):
        self.agent = self._create_agent()
        # MAF agent maintains conversation history internally
        # Only store structured data we extract from conversation
        self.current_plan = None  # Will hold final validated plan

    def _create_agent(self):
        """Create MAF agent with tools"""
        return AzureOpenAIResponsesClient(
            credential=AzureCliCredential(),
        ).create_agent(
            name="InfrastructureOrchestrator",
            instructions=self._get_system_prompt(),
            tools=[
                self._capability_discovery_tool,
                self._naming_suggestion_tool,
                self._cost_estimation_tool,
            ]
        )

    def _get_system_prompt(self) -> str:
        return """You are an infrastructure provisioning orchestrator.

Your job is to:
1. Understand what infrastructure the user wants to provision
2. Ask clarifying questions about:
   - Resource naming (suggest smart defaults, allow override)
   - Budget constraints
   - Naming conventions
   - Region preferences
3. Propose a deployment plan
4. Get user confirmation before executing

Be conversational and helpful. Guide users through the process step-by-step.

Example interaction:
User: "Create a Databricks workspace for ML team"
You: "I'll help you provision a Databricks workspace! A few questions:
1. Which Azure region? (I recommend East US for ML workloads)
2. Resource group name? [suggestion: rg-ml-prod]
3. Any budget constraints?
4. Do you need GPU support?"
"""

    async def process_request(self, user_message: str) -> str:
        """
        Process user message with conversation context.

        MAF agent automatically maintains conversation history,
        so we just pass messages and get responses.

        Returns orchestrator response (may ask clarifying questions).
        """
        # MAF agent handles conversation history internally
        response = await self.agent.run(user_message)

        # Extract response text
        response_text = response.messages[-1].text if response.messages else str(response)

        return response_text

    # Tool definitions (agent can call these)

    def _capability_discovery_tool(self, request: str) -> list[str]:
        """
        Determine which capabilities are needed.

        Called by agent when user intent is clear.
        """
        # For now, simple keyword matching
        # Later: Use LLM to analyze request
        capabilities = []

        if "databricks" in request.lower():
            capabilities.append("provision_databricks")
        if "openai" in request.lower():
            capabilities.append("provision_openai")
        if "firewall" in request.lower():
            capabilities.append("burn_firewall_ports")

        return capabilities

    def _naming_suggestion_tool(self, team: str, env: str, resource_type: str) -> str:
        """Generate smart naming suggestions"""
        naming_map = {
            "resource_group": f"rg-{team}-{env}",
            "workspace": f"{team}-{env}",
            "storage": f"sa{team}{env}001",
        }
        return naming_map.get(resource_type, f"{team}-{env}-{resource_type}")

    def _cost_estimation_tool(self, capability: str, config: dict) -> float:
        """Estimate monthly cost"""
        # Simplified for now
        cost_map = {
            "provision_databricks": 784.00,  # Small cluster
            "provision_openai": 200.00,
            "burn_firewall_ports": 0.00,
        }
        return cost_map.get(capability, 0.0)
```

**Tasks**:
- [ ] Implement `InfrastructureOrchestrator` class
- [ ] Add multi-turn conversation handling (leverage MAF's built-in context)
- [ ] Implement tool definitions (capability discovery, naming, costs)
- [ ] Build CLI integration (`cli_maf.py` - new file, keep old cli.py for reference)
- [ ] Test multi-turn interactions

**Note**: No separate conversation manager needed - MAF agents handle this automatically!

**Test Scenarios**:
1. User says "Create Databricks workspace" → Agent asks clarifying questions
2. User answers questions → Agent proposes plan
3. User customizes plan → Agent updates and confirms
4. User approves → Agent returns validated plan

**Success Criteria**:
- ✅ Orchestrator asks about RG name, budget, constraints
- ✅ Agent suggests smart naming defaults
- ✅ User can override suggestions
- ✅ Conversation maintains context across turns
- ✅ Final plan is validated and ready for execution

**Estimated Time**: 2-3 days

---

### Phase 2: Capability Refactoring (Days 4-6)
**Goal**: Refactor Databricks implementation as MAF-compatible capability

**Structure**:
```
capabilities/
├── __init__.py
├── base.py                       # BaseCapability interface
│
└── databricks/
    ├── __init__.py
    ├── capability.py             # Main capability entry point
    ├── workflow.py               # MAF workflow for provisioning steps
    ├── intent_recognizer.py      # Moved from agent/
    ├── decision_engine.py        # Moved from agent/
    ├── terraform_generator.py    # Moved from agent/
    ├── terraform_executor.py     # Moved from agent/
    └── models.py                 # Databricks-specific models
```

**Key Code** (`capabilities/base.py`):
```python
from abc import ABC, abstractmethod
from typing import Any, Dict, List
from pydantic import BaseModel

class CapabilityRequest(BaseModel):
    """Base request for any capability"""
    capability_name: str
    parameters: Dict[str, Any]
    user_id: str
    session_id: str

class CapabilityPlan(BaseModel):
    """Execution plan for a capability"""
    capability_name: str
    steps: List[str]
    estimated_duration: float  # minutes
    estimated_cost: float  # USD/month
    resources_to_create: List[str]
    requires_approval: bool = True

class CapabilityResult(BaseModel):
    """Result from capability execution"""
    success: bool
    outputs: Dict[str, Any]
    error_message: Optional[str] = None
    execution_time: float  # seconds

class BaseCapability(ABC):
    """
    Base class for all infrastructure capabilities.

    Each capability implements:
    - plan(): Generate execution plan from request
    - execute(): Execute the capability
    - get_clarifying_questions(): Return questions for orchestrator
    """

    @property
    @abstractmethod
    def name(self) -> str:
        """Unique capability name"""
        pass

    @property
    @abstractmethod
    def description(self) -> str:
        """Human-readable description"""
        pass

    @abstractmethod
    async def plan(self, request: CapabilityRequest) -> CapabilityPlan:
        """
        Generate execution plan without executing.

        Returns plan with cost estimates, steps, resources.
        """
        pass

    @abstractmethod
    async def execute(self, plan: CapabilityPlan) -> CapabilityResult:
        """
        Execute the capability based on approved plan.

        Returns result with outputs (URLs, IDs, etc.)
        """
        pass

    @abstractmethod
    def get_clarifying_questions(
        self,
        request: CapabilityRequest
    ) -> List[Dict[str, Any]]:
        """
        Return list of questions to ask user.

        Returns list of questions like:
        [
            {"key": "region", "question": "Which Azure region?",
             "suggestions": ["eastus", "westus2"]},
            {"key": "rg_name", "question": "Resource group name?",
             "suggestion": "rg-team-env"},
        ]
        """
        pass
```

**Key Code** (`capabilities/databricks/capability.py`):
```python
from ..base import BaseCapability, CapabilityRequest, CapabilityPlan, CapabilityResult
from .intent_recognizer import IntentRecognizer
from .decision_engine import DecisionEngine
from .terraform_generator import TerraformGenerator
from .terraform_executor import TerraformExecutor

class DatabricksCapability(BaseCapability):
    """
    Databricks workspace provisioning capability.

    Wraps our existing implementation (Intent → Decision → Generate → Execute)
    in MAF-compatible interface.
    """

    @property
    def name(self) -> str:
        return "provision_databricks"

    @property
    def description(self) -> str:
        return "Provision Azure Databricks workspace with clusters and configuration"

    def __init__(self):
        # Reuse existing components
        self.intent_recognizer = IntentRecognizer()
        self.decision_engine = DecisionEngine()
        self.terraform_generator = TerraformGenerator()
        self.terraform_executor = TerraformExecutor()

    async def plan(self, request: CapabilityRequest) -> CapabilityPlan:
        """
        Generate plan without executing.

        Runs: Intent Recognition → Decision Engine → Returns plan
        """
        # Step 1: Parse request
        infra_request = self.intent_recognizer.recognize_intent(
            request.parameters.get("description", "")
        )

        # Step 2: Make decisions
        decision = self.decision_engine.make_decision(infra_request)

        # Step 3: Return plan
        return CapabilityPlan(
            capability_name=self.name,
            steps=[
                "Create Azure Resource Group",
                "Provision Databricks Workspace",
                "Create Instance Pool",
            ],
            estimated_duration=13.0,  # 13 minutes based on our tests
            estimated_cost=decision.estimated_monthly_cost,
            resources_to_create=[
                f"Resource Group: {decision.resource_group_name}",
                f"Workspace: {decision.workspace_name}",
                f"Instance Pool: {decision.workspace_name}-pool",
            ],
            requires_approval=True,
        )

    async def execute(self, plan: CapabilityPlan) -> CapabilityResult:
        """
        Execute Databricks provisioning.

        Runs: Generate Terraform → Execute Terraform
        """
        try:
            # Generate Terraform files
            terraform_files = self.terraform_generator.generate(...)

            # Execute deployment
            deployment_result = self.terraform_executor.execute(
                terraform_files=terraform_files,
                working_dir=None,  # Use temp dir
                dry_run=False,
            )

            return CapabilityResult(
                success=deployment_result.success,
                outputs={
                    "workspace_url": deployment_result.workspace_url,
                    "workspace_id": deployment_result.workspace_id,
                    "instance_pool_id": deployment_result.instance_pool_id,
                },
                execution_time=deployment_result.deployment_time_seconds,
            )

        except Exception as e:
            return CapabilityResult(
                success=False,
                outputs={},
                error_message=str(e),
                execution_time=0.0,
            )

    def get_clarifying_questions(
        self,
        request: CapabilityRequest
    ) -> List[Dict[str, Any]]:
        """Return questions for orchestrator to ask"""
        return [
            {
                "key": "region",
                "question": "Which Azure region?",
                "suggestions": ["eastus", "westus2", "centralus"],
                "required": True,
            },
            {
                "key": "rg_name",
                "question": "Resource group name?",
                "suggestion": "rg-team-env",
                "required": False,
            },
            {
                "key": "workspace_name",
                "question": "Workspace name?",
                "suggestion": "team-env",
                "required": False,
            },
            {
                "key": "budget_limit",
                "question": "Monthly budget limit? (USD)",
                "suggestion": None,
                "required": False,
            },
        ]
```

**Tasks**:
- [ ] Create `BaseCapability` interface
- [ ] Move existing agent/ files to capabilities/databricks/
- [ ] Implement `DatabricksCapability` wrapper
- [ ] Test capability independently
- [ ] Ensure all existing tests still pass
- [ ] Update imports throughout codebase

**Success Criteria**:
- ✅ Databricks capability implements BaseCapability interface
- ✅ All existing functionality preserved
- ✅ Capability can be instantiated and called independently
- ✅ Plan generation works (without execution)
- ✅ Execution works (actual deployment)
- ✅ All original tests pass

**Estimated Time**: 2-3 days

---

### Phase 3: Capability Registry & Routing (Days 7-8)
**Goal**: Build capability discovery and routing system

**Structure**:
```
orchestrator/
├── capability_registry.py        # NEW: Capability discovery
└── orchestrator_agent.py         # UPDATED: Use registry
```

**Key Code** (`orchestrator/capability_registry.py`):
```python
from typing import Dict, List, Optional
from capabilities.base import BaseCapability
from capabilities.databricks.capability import DatabricksCapability

class CapabilityRegistry:
    """
    Central registry for all infrastructure capabilities.

    Responsibilities:
    - Register capabilities
    - Discover capabilities based on user intent
    - Route requests to appropriate capabilities
    """

    def __init__(self):
        self.capabilities: Dict[str, BaseCapability] = {}
        self._register_default_capabilities()

    def _register_default_capabilities(self):
        """Register built-in capabilities"""
        self.register(DatabricksCapability())
        # Future: self.register(OpenAICapability())
        # Future: self.register(FirewallCapability())

    def register(self, capability: BaseCapability):
        """Register a capability"""
        self.capabilities[capability.name] = capability
        print(f"✓ Registered capability: {capability.name}")

    def get_capability(self, name: str) -> Optional[BaseCapability]:
        """Get capability by name"""
        return self.capabilities.get(name)

    def discover_capabilities(
        self,
        user_request: str
    ) -> List[Dict[str, Any]]:
        """
        Analyze user request and suggest required capabilities.

        For now: Simple keyword matching
        Future: Use LLM to analyze intent

        Returns list like:
        [
            {
                "capability_name": "provision_databricks",
                "confidence": 0.95,
                "reason": "User mentioned 'Databricks workspace'"
            }
        ]
        """
        request_lower = user_request.lower()
        discovered = []

        # Databricks detection
        if any(kw in request_lower for kw in ["databricks", "workspace", "spark"]):
            discovered.append({
                "capability_name": "provision_databricks",
                "confidence": 0.95,
                "reason": "Request mentions Databricks-related keywords"
            })

        # OpenAI detection (future)
        if any(kw in request_lower for kw in ["openai", "gpt", "llm"]):
            discovered.append({
                "capability_name": "provision_openai",
                "confidence": 0.90,
                "reason": "Request mentions OpenAI-related keywords"
            })

        # ML platform = Databricks + OpenAI
        if "ml platform" in request_lower:
            discovered.extend([
                {
                    "capability_name": "provision_databricks",
                    "confidence": 0.95,
                    "reason": "ML platform requires data processing (Databricks)"
                },
                {
                    "capability_name": "provision_openai",
                    "confidence": 0.90,
                    "reason": "ML platform often uses LLM services"
                }
            ])

        return discovered

    def get_all_capabilities(self) -> List[Dict[str, str]]:
        """List all registered capabilities"""
        return [
            {
                "name": cap.name,
                "description": cap.description
            }
            for cap in self.capabilities.values()
        ]
```

**Updated Orchestrator** (`orchestrator/orchestrator_agent.py`):
```python
class InfrastructureOrchestrator:
    def __init__(self):
        self.agent = self._create_agent()
        self.registry = CapabilityRegistry()  # NEW
        self.conversation_history = []
        self.current_plan = None

    async def process_request(self, user_message: str) -> str:
        """Process request with capability discovery"""

        # Step 1: Discover required capabilities
        discovered = self.registry.discover_capabilities(user_message)

        # Step 2: Build conversation with discoveries
        context = f"""
User request: {user_message}

I've identified these capabilities:
{json.dumps(discovered, indent=2)}

Ask the user:
1. Confirm which capabilities to provision
2. For each capability, ask clarifying questions
3. Suggest smart defaults for names, regions, etc.
"""

        # Step 3: Get agent response
        response = await self.agent.run(context)

        return response
```

**Tasks**:
- [ ] Implement `CapabilityRegistry` class
- [ ] Add capability discovery logic (keyword-based for now)
- [ ] Integrate registry into orchestrator
- [ ] Test discovery with various inputs
- [ ] Add "propose and confirm" workflow

**Test Scenarios**:
1. User: "Deploy Databricks" → Discovers 1 capability
2. User: "ML platform" → Discovers 2 capabilities (Databricks + OpenAI)
3. User confirms subset → Only execute confirmed capabilities

**Success Criteria**:
- ✅ Registry discovers correct capabilities for requests
- ✅ Orchestrator proposes capabilities to user
- ✅ User can confirm/modify capability list
- ✅ Multi-capability scenarios work (even if only 1 capability implemented)

**Estimated Time**: 1-2 days

---

### Phase 4: Integration & Polish (Days 9-10)
**Goal**: End-to-end testing, documentation, demo preparation

**Tasks**:
- [ ] End-to-end test: User request → Conversation → Plan → Approval → Deployment
- [ ] Error handling improvements
- [ ] Add comprehensive logging
- [ ] Write user guide (how to use new CLI)
- [ ] Create demo script
- [ ] Record demo video/screenshots
- [ ] Update README.md
- [ ] Clean up deprecated code (old agent/ directory)

**Demo Script**:
```bash
# 1. Start CLI
python cli_maf.py

# 2. Natural language request
> Create a Databricks workspace for ML team

# 3. Agent asks clarifying questions
Agent: I'll help you provision a Databricks workspace! A few questions:
1. Which Azure region? (I recommend East US for ML workloads)
> East US

2. Resource group name? [suggestion: rg-ml-prod]
> rg-production-ml

3. Any budget constraints?
> Keep it under $1000/month

# 4. Agent proposes plan
Agent: Here's what I'll provision:
- Resource Group: rg-production-ml
- Databricks Workspace: ml-prod
- Instance Pool: Standard_D4s_v5 (small, cost-optimized)
- Estimated Cost: $784/month ✓ (within budget)
- Deployment Time: ~13 minutes

Proceed? (yes/no/customize)
> yes

# 5. Execute deployment
Agent: Provisioning infrastructure...
[Progress bar]
✓ Resource Group created
✓ Databricks Workspace created
✓ Instance Pool created

Success! Your workspace is ready:
- URL: https://adb-123456.azuredatabricks.net
- Time: 13m 2s
- Cost: $784/month
```

**Success Criteria**:
- ✅ End-to-end deployment works
- ✅ Demo script runs smoothly
- ✅ Documentation is clear and complete
- ✅ Code is clean and well-commented
- ✅ Ready to present to team

**Estimated Time**: 2 days

---

## 5. Key Technical Decisions

### Decision 1: Agent vs Workflow for Orchestrator

**Question**: Should orchestrator be a simple Agent or a complex Workflow?

**Recommendation**: **Start with Agent, migrate to Workflow if needed**

**Rationale**:
- Agent is simpler for conversational interaction
- Agent can use tools (capabilities) directly
- Workflow adds complexity (graph management, node connections)
- Workflow needed if: Multiple parallel capabilities, complex dependencies, checkpointing required

**Implementation**:
```python
# Phase 1-3: Agent-based orchestrator
orchestrator = InfrastructureOrchestrator()  # Agent internally
response = await orchestrator.process_request("Deploy Databricks")

# Future (if needed): Workflow-based orchestrator
workflow = InfrastructureOrchestrationWorkflow()
result = await workflow.run("Deploy Databricks")
```

### Decision 2: Capability as Agent vs Workflow

**Question**: Should each capability be an Agent or Workflow?

**Recommendation**: **Capability = Wrapper class that MAY use Agent/Workflow internally**

**Rationale**:
- DatabricksCapability: Current pipeline is linear → No need for Agent/Workflow, just wrap existing code
- Future OpenAICapability: Might need Agent for decision-making
- Future complex capabilities: Might need Workflow for multi-step orchestration

**Implementation**:
```python
# Simple capability (Databricks - no Agent needed)
class DatabricksCapability(BaseCapability):
    def __init__(self):
        self.intent_recognizer = IntentRecognizer()  # Existing
        self.decision_engine = DecisionEngine()      # Existing
        # ... wrap existing components

# Complex capability (future - uses Agent internally)
class OpenAICapability(BaseCapability):
    def __init__(self):
        self.agent = self._create_planning_agent()  # MAF Agent for planning

    def _create_planning_agent(self):
        return AzureOpenAIResponsesClient(...).create_agent(...)
```

### Decision 3: State Management

**Question**: Use MAF's built-in state or custom?

**Recommendation**: **Use MAF's conversation context (built-in), minimal custom state**

**Rationale**:
- **MAF Agents maintain conversation history automatically** - no manual tracking needed
- Phase 0 validated this works perfectly (Test 5 showed context preservation)
- Only store structured data extracted from conversation (e.g., final validated plan)
- Good enough for spike (single-session)
- Production: Can add MAF's checkpointing or custom DB persistence later if needed

**What We DON'T Need in Phase 1**:
- ❌ Manual conversation history tracking - MAF does this
- ❌ ConversationManager class - unnecessary, MAF agent IS the manager
- ❌ Persistent state/database - single CLI session is fine
- ❌ Complex state machine - MAF handles conversation flow

**Implementation**:
```python
# Phase 1: Let MAF handle conversation state
class InfrastructureOrchestrator:
    def __init__(self):
        self.agent = self._create_agent()
        self.current_plan = None  # Only store final extracted plan

    async def process_request(self, user_message: str) -> str:
        # MAF agent maintains full conversation context internally
        response = await self.agent.run(user_message)
        return response.messages[-1].text

# Future (Phase 3+): Add persistence if multi-session needed
workflow.save_checkpoint("session_123.json")
workflow.load_checkpoint("session_123.json")
```

### Decision 4: Tool Calling vs Direct Method Calls

**Question**: Should orchestrator invoke capabilities via MAF tools or direct Python calls?

**Recommendation**: **Hybrid: Discovery via tools, Execution via direct calls**

**Rationale**:
- MAF tools good for: Dynamic discovery, LLM-driven decisions
- Direct calls good for: Predictable execution, easier debugging

**Implementation**:
```python
# Discovery: Agent uses tool
@agent.tool
def discover_capabilities(request: str) -> list[str]:
    return registry.discover_capabilities(request)

# Execution: Direct call
capability = registry.get_capability("provision_databricks")
result = await capability.execute(plan)
```

---

## 6. Risk Mitigation

### Risk 1: MAF Learning Curve
**Mitigation**: Start with simple Agent, use extensive examples from GitHub repo

### Risk 2: Breaking Existing Functionality
**Mitigation**: Keep old code in `agent/` directory, comprehensive testing after each phase

### Risk 3: Over-Engineering
**Mitigation**: Follow "Phase by Phase" approach, validate at each step, don't build unnecessary abstractions

### Risk 4: MAF Version Instability (pre-release)
**Mitigation**: Pin exact version in requirements.txt, document any workarounds

---

## 7. Success Metrics

### Technical Metrics
- ✅ All existing tests pass after refactor
- ✅ End-to-end deployment works in <15 minutes
- ✅ Orchestrator asks 3-5 clarifying questions
- ✅ User can customize 100% of suggested values
- ✅ Code coverage ≥90%

### Demo Metrics
- ✅ Natural conversational flow (feels like chatbot)
- ✅ Clear visualization of capabilities and routing
- ✅ Successful deployment shown live
- ✅ Code walkthrough explains architecture clearly

### Quality Metrics
- ✅ Code is presentable to team (clean, documented)
- ✅ Architecture is extensible (easy to add capabilities)
- ✅ No "brute force" implementations
- ✅ Follows MAF conventions and patterns

---

## 8. Next Steps

### Immediate Actions (Next 1 Hour)
1. ✅ Install MAF: `pip install agent-framework --pre`
2. ✅ Create `tests/test_maf_setup.py` and validate connectivity
3. ✅ Review MAF GitHub examples: `python/samples/getting_started/agents/`
4. ✅ Create Phase 0 branch: `git checkout -b feature/maf-phase0-setup`

### Phase 0 Checklist (Today)
- [ ] Install agent-framework package
- [ ] Verify Azure OpenAI connectivity with MAF
- [ ] Create test agent and confirm basic interaction
- [ ] Review MAF samples for patterns
- [ ] Document any setup issues/workarounds

### Ready to Start?
Once Phase 0 is complete and validated, we'll proceed to Phase 1 (Conversational Orchestrator).

**Questions before we begin?**

---

## 9. Resources

- **MAF Docs**: https://learn.microsoft.com/en-us/agent-framework/
- **GitHub Repo**: https://github.com/microsoft/agent-framework
- **Python Samples**: https://github.com/microsoft/agent-framework/tree/main/python/samples
- **Discord**: https://discord.gg/b5zjErwbQM (for questions)
- **PyPI**: https://pypi.org/project/agent-framework/

---

**Status**: Ready for Phase 0 - Pending your approval to proceed! 🚀
