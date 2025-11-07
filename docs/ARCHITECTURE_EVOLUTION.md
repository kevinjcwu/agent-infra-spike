# Architecture Evolution: From Single-Purpose Agent to Multi-Capability Platform

**Date**: November 6, 2025
**Status**: Planning Phase
**Context**: Evolution from Databricks provisioning spike to enterprise orchestration platform

---

## 1. Current State (Spike Implementation)

### Architecture Overview
```
User Input → Orchestrator → Capability → Agent Modules → Terraform → Deployed Resources
```

**Characteristics:**
- ✅ Conversational interface: Multi-turn clarification and parameter gathering
- ✅ MAF-based orchestration: Microsoft Agent Framework handles conversation context
- ✅ Tool-enabled: Dynamic tool registration (select_capabilities, suggest_naming, estimate_cost, execute_deployment)
- ✅ Capability pattern: Pluggable BaseCapability interface for infrastructure provisioning
- ✅ Single capability: Databricks workspace provisioning (Resource Group + Workspace + Cluster as unit)
- ✅ Proven deployment: Successfully deployed to Azure in ~13 minutes end-to-end

**Current Implementation Status:**
- ✅ Phase 0: MAF integration with Azure OpenAI (completed)
- ✅ Phase 1: Multi-turn conversational orchestrator with tools (completed)
- ✅ Phase 1.5: Tool Registry pattern for scalable tool management (completed)
- ✅ Phase 1.6: Capability Registry pattern for hallucination prevention (completed)
- ✅ Phase 2: Capability integration with BaseCapability interface (completed)
- ✅ Actual Azure deployment: Verified working with real infrastructure

**Remaining Spike Limitations:**
- ⚠️ Single capability only (Databricks) - by design for spike
- ⚠️ In-memory conversation state (lost on restart)
- ⚠️ No multi-capability workflows
- ⚠️ Basic error handling (no rollback orchestration)

---

### Understanding Current Architecture: `agent/` vs `capabilities/`

**TL;DR**: `agent/` contains the actual deployment code, `capabilities/` provides a standard interface wrapper so the orchestrator can invoke it in a pluggable way. They work together.

#### `agent/` Directory - The Real Worker (ACTIVE)

This is where all the **actual deployment logic** lives:

```
agent/
├── intent_recognizer.py      # LLM: Parse natural language → InfrastructureRequest
├── decision_engine.py         # Logic: GPU or CPU? Premium or Standard? Sizing?
├── terraform_generator.py     # Generate: Create Terraform HCL from decisions
├── terraform_executor.py      # Execute: Run terraform init/plan/apply
├── models.py                  # Data: InfrastructureRequest, InfrastructureDecision
└── config.py                  # Config: Azure credentials and settings
```

**What it deploys (as one atomic unit)**:
1. Azure Resource Group (e.g., `rg-ml-team-prod`)
2. Azure Databricks Workspace (e.g., `ml-prod`)
3. Databricks Cluster inside workspace (e.g., `ml-prod-cluster`)

**Status**: ✅ **ACTIVE** - This code is running in production and does all deployment work

#### `capabilities/` Directory - The Interface Wrapper (NEW)

This provides a **standard interface** for the orchestrator:

```
capabilities/
├── base.py                           # BaseCapability interface
└── databricks/
    └── capability.py                 # DatabricksCapability wraps agent/
```

**What `capabilities/databricks/capability.py` does**:
```python
class DatabricksCapability(BaseCapability):
    def __init__(self):
        # Import and instantiate agent modules
        self.intent_recognizer = IntentRecognizer()      # from agent/
        self.decision_engine = DecisionEngine()          # from agent/
        self.terraform_generator = TerraformGenerator()  # from agent/
        self.terraform_executor = TerraformExecutor()    # from agent/

    async def plan(self, context: CapabilityContext) -> CapabilityPlan:
        """Generate deployment plan (dry-run)"""
        # Step 1: Parse parameters using agent/intent_recognizer.py
        request = self.intent_recognizer.recognize_intent(...)

        # Step 2: Make configuration decisions using agent/decision_engine.py
        decision = self.decision_engine.make_decision(request)

        # Step 3: Generate Terraform using agent/terraform_generator.py
        terraform_files = self.terraform_generator.generate(decision)

        # Step 4: Run terraform plan using agent/terraform_executor.py
        plan_result = self.terraform_executor.execute_deployment(dry_run=True)

        # Step 5: Package as standard CapabilityPlan
        return CapabilityPlan(
            resources=...,
            estimated_cost=...,
            terraform_details=...
        )

    async def execute(self, plan: CapabilityPlan) -> CapabilityResult:
        """Execute approved plan"""
        # Use agent/terraform_executor.py for actual deployment
        result = self.terraform_executor.execute_deployment(dry_run=False)
        return CapabilityResult(success=True, outputs=result.outputs)
```

**Status**: ✅ **NEW WRAPPER** - Adds standard interface, delegates all work to agent/

#### Why This Design?

**Problem Solved**: Orchestrator and agent had incompatible interfaces

**Before**:
```python
# Orchestrator (MAF-based, async, conversational)
orchestrator.process_message("I need Databricks")
    ↓
    ❌ How do we call the agent?
    ❌ Agent expects different input format
    ❌ Agent doesn't support plan-then-execute flow
```

**After**:
```python
# Orchestrator → Capability → Agent
orchestrator.execute_capability("provision_databricks", params)
    ↓
capability.plan(context)  # Standard interface
    ↓
agent modules do actual work:
  - intent_recognizer.recognize_intent()
  - decision_engine.make_decision()
  - terraform_generator.generate()
  - terraform_executor.execute_deployment()
```

**Benefits**:
1. **Orchestrator stays simple**: Just calls `capability.plan()` and `capability.execute()`
2. **Agent code unchanged**: All Databricks logic remains exactly as it was
3. **Extensible**: Want OpenAI provisioning? Create `capabilities/openai/` with same interface
4. **Testable**: Each layer can be tested independently

#### Data Flow: User Request → Deployed Infrastructure

```
User: "I need Databricks for ML team in production"
    ↓
┌─────────────────────────────────────────────────────────────┐
│ ORCHESTRATOR (orchestrator/orchestrator_agent.py)          │
│ • Multi-turn conversation (MAF framework)                   │
│ • Uses tools: select_capabilities, suggest_naming,          │
│              estimate_cost, execute_deployment              │
│ • Gathers parameters: team, environment, region, names      │
│ • Calls: capability.plan() then capability.execute()        │
└────────────────────┬────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────┐
│ CAPABILITY WRAPPER (capabilities/databricks/capability.py)  │
│                                                             │
│ plan() method:                                              │
│   1. Build request text from context parameters            │
│   2. Call agent/intent_recognizer.py                        │
│   3. Call agent/decision_engine.py                          │
│   4. Call agent/terraform_generator.py                      │
│   5. Call agent/terraform_executor.py (dry-run)             │
│   6. Extract resources, costs, terraform files              │
│   7. Return CapabilityPlan                                  │
│                                                             │
│ execute() method:                                           │
│   1. Reconstruct TerraformFiles from plan                   │
│   2. Call agent/terraform_executor.py (apply)               │
│   3. Return CapabilityResult with workspace URL             │
└────────────────────┬────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────┐
│ AGENT MODULES (agent/)                                      │
│                                                             │
│ intent_recognizer.py:                                       │
│   • Parse: "ML team prod" → InfrastructureRequest           │
│                                                             │
│ decision_engine.py:                                         │
│   • Decide: ML workload → GPU instances (NC6s_v3)           │
│   • Decide: Production → Premium Databricks SKU             │
│   • Calculate: Cluster sizing (2-8 workers)                 │
│                                                             │
│ terraform_generator.py:                                     │
│   • Generate: main.tf, variables.tf, outputs.tf,            │
│              provider.tf, terraform.tfvars                  │
│   • Use templates: templates/*.tf.j2                        │
│                                                             │
│ terraform_executor.py:                                      │
│   • Write files to working directory                        │
│   • Run: terraform init                                     │
│   • Run: terraform plan (dry-run) or apply (execute)       │
│   • Parse outputs: workspace_url, workspace_id              │
└────────────────────┬────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────┐
│ AZURE RESOURCES (Deployed)                                  │
│ 1. Resource Group: rg-ml-team-prod                          │
│ 2. Databricks Workspace: ml-prod                            │
│    URL: https://adb-xxxx.azuredatabricks.net                │
│ 3. Databricks Cluster: ml-prod-cluster (GPU instances)      │
└─────────────────────────────────────────────────────────────┘
```

#### Is `agent/` Deprecated?

**NO!** ❌

The `agent/` directory is **ACTIVE** and does all the deployment work. The "deprecated" comment in earlier docs was **aspirational** (thinking ahead to possible future refactoring), not actual current status.

**Current Reality**:
- ✅ `agent/` code is **ACTIVE** - runs in production
- ✅ `capabilities/` code **WRAPS** agent modules
- ✅ They work **TOGETHER** - not replacing each other

**Future Possibility** (Phase 4+, maybe):
- 🤔 Could refactor agent modules directly into capabilities/databricks/
- 🤔 Could extract common utilities to capabilities/common/
- 🤔 Could keep agent/ as is (if it works, why change it?)

**Decision for Spike**: Keep `agent/` as is. It's proven, tested, and works perfectly. The capability wrapper adds exactly what we need (standard interface) without requiring refactoring.

#### Single Capability Design Decision

**Current**: Deploy 3 resources as one atomic unit

```
DatabricksCapability
    ↓
Provisions (all together):
    1. Azure Resource Group
    2. Azure Databricks Workspace
    3. Databricks Cluster
```

**Why Not Separate Capabilities?**

**Option 1: Single Capability** ✅ (Current)
```
capabilities/databricks/  # Deploys RG + Workspace + Cluster together
```

**Pros**:
- Simple: One capability = one user request
- Logical: Can't have cluster without workspace, workspace without RG
- Atomic: Deploy or rollback as a unit
- Matches user intent: "I need Databricks" = workspace + cluster ready to use

**Option 2: Granular Capabilities** ❌ (Too Complex)
```
capabilities/azure_resource_group/
capabilities/databricks_workspace/
capabilities/databricks_cluster/
```

**Cons**:
- Complex: Orchestrator must coordinate 3 capabilities
- Dependencies: Cluster requires workspace ID, workspace requires RG name
- User confusion: "I just wanted Databricks, why 3 requests?"
- Error-prone: What if workspace succeeds but cluster fails?

**Recommendation**: ✅ Keep single capability for spike. This is the right design for the use case.

---

### Current File Structure

```
agent-infra-spike/
├── orchestrator/                    # MAF-based conversational orchestrator
│   ├── __init__.py
│   ├── orchestrator_agent.py        # Main conversational agent
│   ├── capability_registry.py       # Infrastructure capability validation
│   ├── tool_manager.py              # Dynamic tool registration system
│   ├── tools.py                     # Orchestrator tools (4 tools implemented)
│   └── models.py                    # Orchestrator data models
│
├── capabilities/                    # Pluggable infrastructure capabilities
│   ├── __init__.py                  # Exports BaseCapability, data models
│   ├── base.py                      # BaseCapability interface definition
│   │                                # (CapabilityContext, CapabilityPlan, CapabilityResult)
│   └── databricks/                  # Databricks provisioning capability
│       ├── __init__.py
│       └── capability.py            # DatabricksCapability wraps agent/
│
├── agent/                           # Actual deployment code (ACTIVE)
│   ├── __init__.py
│   ├── infrastructure_agent.py      # Legacy single-shot interface
│   ├── intent_recognizer.py         # LLM-based request parsing
│   ├── decision_engine.py           # Configuration decision logic
│   ├── terraform_generator.py       # HCL file generation from templates
│   ├── terraform_executor.py        # Terraform CLI execution
│   ├── models.py                    # InfrastructureRequest, Decision, Result
│   └── config.py                    # Azure credentials and settings
│
├── templates/                       # Terraform Jinja2 templates
│   ├── main.tf.j2                   # Resource definitions
│   ├── variables.tf.j2              # Variable declarations
│   ├── outputs.tf.j2                # Output definitions
│   ├── provider.tf.j2               # Azure provider config
│   └── terraform.tfvars.j2          # Variable values
│
├── cli_maf.py                       # 🎯 Conversational CLI (USE THIS)
├── tests/                           # Test suite organized by phase
│   ├── test_orchestrator.py         # Phase 1: Orchestrator + tools
│   ├── test_capability_integration.py  # Phase 2: Capability integration
│   ├── test_maf_setup.py            # Phase 0: MAF validation
│   └── test_*.py                    # Legacy agent tests
│
└── docs/                            # Documentation
    ├── PRD.md                       # Product requirements
    ├── ARCHITECTURE_EVOLUTION.md    # This file
    ├── MAF_RESEARCH_AND_IMPLEMENTATION_PLAN.md
    └── implementation_status/       # Phase-by-phase progress

```

---

## 2. Target State (Enterprise Platform)

### Architecture Overview (From Diagram)

```
┌─────────────────────────────────────────────────────────────────────────┐
│                          PERSONAS & DEVICES                              │
│  DevOps Engineer ──┐                                                     │
│  Data Engineer ────┤─── CLI / Chat Interface                            │
│  ML Engineer ──────┘                                                     │
└───────────────────────────────┬─────────────────────────────────────────┘
                                │
                                ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                        ORCHESTRATOR AGENT                                │
│  ┌──────────────────────────────────────────────────────────────────┐  │
│  │  1. Plan the execution workflow for the user request            │  │
│  │  2. Validate the execution workflow with the user               │  │
│  │  3. Execute the capability flow (invoke agents/tools)           │  │
│  └──────────────────────────────────────────────────────────────────┘  │
│                                                                          │
│  State Management: Session notes, execution history                     │
│  User Validation: Clarifying questions, approval gates                  │
│  Capability Routing: Determine which capabilities needed                │
└───────────────────────────────┬─────────────────────────────────────────┘
                                │
                                ▼
                    Invoke / Continue Capability Flow
                                │
                                ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                           CAPABILITIES                                   │
│  ┌──────────────────────┬────────────────────┬─────────────────────┐  │
│  │  Provisioning        │  Provisioning      │  Burn Firewall      │  │
│  │  Open AI Env         │  Data Bricks       │  Ports              │  │
│  └──────────────────────┴────────────────────┴─────────────────────┘  │
│                                                                          │
│  Each capability = Multi-agent system OR MCP tool                       │
│  Pluggable architecture: Add new capabilities without core changes      │
└─────────────────────────────────────────────────────────────────────────┘
                                │
                                ▼
           ┌────────────────────┴────────────────────┐
           ▼                                          ▼
┌───────────────────────────┐          ┌───────────────────────────┐
│  CAPABILITY WORKFLOW       │          │  CAPABILITY WORKFLOW      │
│  (e.g., Provision OpenAI)  │          │  (e.g., Provision DBX)    │
│                            │          │                           │
│  ┌──────────────────────┐ │          │  Current Implementation:  │
│  │ Step 1 (needs LLM)   │ │          │  - Intent Recognizer      │
│  │ Human Executor       │ │          │  - Decision Engine        │
│  ├──────────────────────┤ │          │  - Terraform Generator    │
│  │ Step 2 (no LLM)      │ │          │  - Terraform Executor     │
│  │ AI Agent             │ │          │                           │
│  ├──────────────────────┤ │          │  Multi-step with AI at    │
│  │ Step N               │ │          │  selective steps          │
│  └──────────────────────┘ │          └───────────────────────────┘
│                            │
│  State: Save execution     │
│         state between      │
│         steps              │
└───────────────────────────┘
```

### Key Architectural Changes

#### **Change 1: Conversational Orchestrator**
**Current:** Single-shot parsing with auto-generated defaults
**Target:** Multi-turn conversation with user validation

```
User: "Create a production workspace for ML team"

Orchestrator: "I'll help you provision a Databricks workspace. Let me confirm:
- Team: ML
- Environment: Production
- Region: Not specified. Which Azure region? (eastus/westus2/centralus)"

User: "East US"

Orchestrator: "Great! A few more details:
- Resource Group name: [auto-suggestion: rg-ml-prod] - Keep or customize?
- Workspace name: [auto-suggestion: ml-prod] - Keep or customize?
- Cluster configuration:
  * ML workload detected → GPU instances recommended
  * Cluster size: 2-8 workers (adjustable)
  * Estimated cost: $3,200/month

Would you like to:
1. Proceed with these settings
2. Customize cluster size
3. Review alternative instance types"

User: "Name the resource group rg-ml-team-prod and reduce cluster to 1-4 workers"

Orchestrator: "Updated:
- Resource Group: rg-ml-team-prod ✓
- Workspace: ml-prod ✓
- Cluster: 1-4 workers (reduces cost to ~$2,100/month) ✓

Ready to deploy? This will:
1. Create resource group in East US
2. Provision Databricks workspace (Premium SKU)
3. Create GPU instance pool with NC6s_v3 instances
4. Deploy autoscaling cluster (1-4 workers)

Type 'yes' to confirm or 'no' to make changes."
```

**Implementation Requirements:**
- Session state management (track conversation context)
- Clarifying question generation (LLM-driven)
- User input validation and parsing
- Multi-turn interaction loop
- Default suggestion system with override capability

---

#### **Change 2: Capability Registry & Router**
**Current:** Hardcoded Databricks logic
**Target:** Pluggable capability system

```python
# Capability Registry (new)
class CapabilityRegistry:
    """
    Central registry for all available infrastructure capabilities.
    Each capability is either:
    - A multi-agent system (complex workflows)
    - An MCP tool (simpler operations)
    """

    capabilities = {
        "provision_databricks": {
            "type": "multi_agent",
            "module": "capabilities.databricks.agent",
            "description": "Provision Databricks workspace with clusters and configuration",
            "parameters": ["team", "environment", "region", "workspace_name", "cluster_config"],
            "tags": ["databricks", "azure", "analytics"]
        },
        "provision_openai": {
            "type": "multi_agent",
            "module": "capabilities.openai.agent",
            "description": "Provision Azure OpenAI service with deployments",
            "parameters": ["service_name", "region", "deployments", "tier"],
            "tags": ["openai", "azure", "ai"]
        },
        "burn_firewall_ports": {
            "type": "mcp_tool",
            "module": "capabilities.firewall.tool",
            "description": "Open firewall ports for specific services",
            "parameters": ["ports", "source_ips", "destination", "protocol"],
            "tags": ["networking", "security", "firewall"]
        }
    }

    def find_capabilities(self, user_request: str) -> list[str]:
        """Use LLM to determine which capabilities are needed"""
        # LLM analyzes request and returns capability IDs
        pass
```

**Orchestrator Logic:**
```python
class OrchestratorAgent:
    """
    Main orchestrator that:
    1. Understands user intent
    2. Plans execution workflow (which capabilities needed)
    3. Validates plan with user
    4. Executes capabilities in sequence
    5. Manages state across multi-step workflows
    """

    def process_request(self, user_request: str) -> WorkflowPlan:
        # Step 1: Analyze request
        intent = self.analyze_intent(user_request)

        # Step 2: Determine required capabilities
        capabilities = self.registry.find_capabilities(user_request)

        # Step 3: Generate execution plan
        plan = self.create_workflow_plan(intent, capabilities)

        # Step 4: Validate with user (MULTI-TURN CONVERSATION)
        validated_plan = self.validate_with_user(plan)

        # Step 5: Execute capability flow
        result = self.execute_plan(validated_plan)

        return result

    def validate_with_user(self, plan: WorkflowPlan) -> WorkflowPlan:
        """
        Interactive validation loop.
        Ask clarifying questions until all parameters confirmed.
        """
        while not plan.is_fully_specified():
            # Generate clarifying question
            question = self.generate_clarification(plan)

            # Get user input
            answer = self.get_user_input(question)

            # Update plan
            plan = self.incorporate_answer(plan, answer)

        # Final confirmation
        if not self.get_final_approval(plan):
            return self.validate_with_user(plan)  # Loop again

        return plan
```

---

#### **Change 3: Capability Workflow Engine**
**Current:** Linear pipeline (Intent → Decision → Generate → Execute)
**Target:** Flexible multi-step workflow with conditional LLM usage

```python
class CapabilityWorkflow:
    """
    Base class for capability workflows.
    Each step can optionally use LLM, run synchronously/async,
    require user input, etc.
    """

    steps: list[WorkflowStep]

    def execute(self, context: ExecutionContext) -> WorkflowResult:
        """Execute all steps in sequence, managing state"""
        for step in self.steps:
            if step.requires_llm:
                result = self.execute_llm_step(step, context)
            else:
                result = self.execute_code_step(step, context)

            # Save state after each step
            context.save_state(step.id, result)

            # Check for user validation requirement
            if step.requires_user_approval:
                if not self.get_user_approval(step, result):
                    return WorkflowResult.cancelled()

        return WorkflowResult.success()


# Example: Databricks Provisioning Capability
class DatabricksProvisioningWorkflow(CapabilityWorkflow):
    """
    Multi-step workflow for Databricks provisioning.
    Maps to our current implementation but more flexible.
    """

    steps = [
        WorkflowStep(
            id="parse_requirements",
            name="Parse Requirements",
            requires_llm=True,  # Uses Intent Recognizer
            executor=IntentRecognizer()
        ),
        WorkflowStep(
            id="make_decisions",
            name="Configuration Decisions",
            requires_llm=False,  # Pure business logic
            executor=DecisionEngine()
        ),
        WorkflowStep(
            id="generate_terraform",
            name="Generate Terraform",
            requires_llm=False,  # Template rendering
            executor=TerraformGenerator()
        ),
        WorkflowStep(
            id="show_plan",
            name="Review Plan",
            requires_llm=False,
            requires_user_approval=True,  # Approval gate
            executor=TerraformExecutor(dry_run=True)
        ),
        WorkflowStep(
            id="deploy",
            name="Deploy Infrastructure",
            requires_llm=False,
            executor=TerraformExecutor(apply=True)
        )
    ]
```

---

## 3. Clarifying Questions

### **Q1: Orchestrator LLM Usage**
**Question:** Should the orchestrator agent use a different LLM approach than our current OpenAI Function Calling?

**Current approach:** Direct OpenAI Function Calling for structured extraction
**Options for orchestrator:**
- **A)** Same approach (OpenAI Function Calling for each decision point)
- **B)** Microsoft Agent Framework (MAF) for multi-turn conversations
- **C)** Semantic Kernel for orchestration + OpenAI for individual steps
- **D)** Custom state machine with LLM calls at specific points

**My recommendation:** Start with (A) for consistency, migrate to (C) if complexity grows. MAF adds overhead but gives us:
- Built-in conversation memory
- Multi-turn interaction patterns
- Agent-to-agent communication primitives

**Your preference?**

---

### **Q2: Clarifying Questions - Scope**
**Question:** How deep should clarifying questions go?

**Options:**
- **Minimal:** Only ask about required fields with no defaults (e.g., region if not specified)
- **Moderate:** Ask about names, sizing, costs - let user customize key parameters
- **Comprehensive:** Ask about every configurable parameter (tags, networking, permissions, etc.)

**Example scenarios:**

**Minimal:**
```
User: "Create workspace for ML team"
Agent: "Which region? (eastus/westus2)"
User: "East US"
Agent: "Deploying with default names and configuration..."
```

**Moderate (Recommended):**
```
User: "Create workspace for ML team"
Agent: "I'll create a dev workspace for ML team. A few questions:
1. Which region? (eastus/westus2/centralus)
2. Resource group name? [suggestion: rg-ml-dev]
3. Workspace name? [suggestion: ml-dev]
4. Cluster size? [suggestion: 1-2 workers for dev, ~$784/month]"
```

**Comprehensive:**
```
User: "Create workspace for ML team"
Agent: "Let's configure your workspace. Please specify:
1. Region
2. Resource group name
3. Workspace name
4. Databricks SKU (standard/premium)
5. Cluster configuration (instance types, worker count, autoscaling)
6. Network configuration (VNet integration? Public/private endpoints?)
7. Tags (project, owner, cost center, end date)
8. Security settings (SCIM, AAD integration, IP access lists)
9. Storage configuration (ADLS Gen2 integration?)
..."
```

**Your preference?** I recommend **Moderate** - balance between user control and reasonable defaults.

---

### **Q3: Resource Naming Conventions**
**Question:** Should naming be:
- **Auto-generated only** (current: `{team}-{env}`)
- **User-provided only** (agent asks for every name)
- **Smart suggestions with override** (agent suggests, user can customize)

**Example interaction with smart suggestions:**
```
Agent: "I'll create these resources:
- Resource Group: rg-ml-team-prod
- Workspace: ml-prod-workspace
- Instance Pool: ml-prod-pool
- Storage: samlprod001

Would you like to customize any names? (type 'yes' or hit Enter to proceed)"

User: "yes, change resource group to rg-production-ml"

Agent: "Updated! Resource Group: rg-production-ml ✓
Proceeding with other suggested names..."
```

**Your preference?**

---

### **Q4: Capability Discovery**
**Question:** How does the orchestrator decide which capabilities to use?

**Scenario:** User says "Deploy a complete ML platform in East US"

**Options:**
- **A) Explicit capability names:** User must say "provision databricks AND provision openai"
- **B) Intent-based routing:** Orchestrator infers: "ML platform = Databricks + OpenAI + maybe firewall rules"
- **C) Hybrid:** Orchestrator proposes capabilities, user confirms/modifies

**Example (Option C - Recommended):**
```
User: "Deploy ML platform for data science team in East US"

Orchestrator: "An ML platform typically requires:
1. ✓ Databricks workspace (for data processing and ML training)
2. ✓ Azure OpenAI service (for LLM integration)
3. ? Azure Machine Learning workspace (for model registry)
4. ? Firewall rules (if connecting to on-prem data sources)

I recommend capabilities 1 and 2. Do you need 3 or 4?"

User: "Just 1 and 2"

Orchestrator: "Perfect! I'll provision:
- Databricks workspace
- Azure OpenAI service (GPT-4o deployment)

Let me ask a few questions about each..."
```

**Your preference?**

---

### **Q5: Agent-to-Agent vs MCP Tools**
**Question:** When should a capability be a multi-agent system vs an MCP tool?

**My understanding from diagram:**
- **Multi-agent:** Complex workflows with multiple steps, some needing LLM reasoning
- **MCP tool:** Simpler operations, mostly deterministic

**Examples I'd classify:**

**Multi-Agent Systems:**
- ✅ Provision Databricks (needs cost optimization decisions, cluster sizing logic)
- ✅ Provision OpenAI (needs deployment planning, quota management)
- ✅ Deploy ML pipeline (needs workflow orchestration, dependency management)

**MCP Tools:**
- ✅ Burn firewall ports (straightforward: open ports X, Y, Z)
- ✅ Create Azure AD group (deterministic: group name, members)
- ✅ Update DNS records (simple CRUD operation)

**Gray area:**
- 🤔 Provision storage account (simple creation BUT might need access policy decisions)
- 🤔 Configure monitoring (simple alerts BUT might need intelligent threshold selection)

**Your criteria for this decision?**

---

### **Q6: State Management**
**Question:** Where is state stored between orchestrator steps?

**Options:**
- **In-memory** (current spike approach - lost on restart)
- **File-based** (JSON/YAML in working directory)
- **Database** (PostgreSQL/CosmosDB for production)
- **Azure Storage** (Blob storage for session state)

**State to persist:**
- Conversation history
- User confirmations
- Workflow execution progress
- Capability outputs (e.g., workspace URL after deployment)
- Approval audit trail

**For MVP enhancement:** I'd recommend **file-based** (extend current working directory approach)
**For production platform:** Database with proper session management

**Your preference?**

---

### **Q7: Validation Checkpoints**
**Question:** How many validation gates in a workflow?

**Current:** Single approval gate before Terraform apply

**Options for multi-capability workflow:**
- **A) Per-capability:** Approve each capability individually (e.g., approve Databricks, then approve OpenAI)
- **B) Per-workflow-plan:** Approve entire plan once upfront, execute all
- **C) Hybrid:** Approve plan, then confirm at critical steps (e.g., before production deployments)

**Example (Option C):**
```
1. Orchestrator proposes plan → USER APPROVES
2. Execute Databricks provisioning → Success
3. About to execute OpenAI provisioning (costs $$$) → USER CONFIRMS
4. Execute OpenAI provisioning → Success
5. About to burn firewall ports (security change) → USER CONFIRMS
```

**Your preference?**

---

### **Q8: Error Handling & Rollback**
**Question:** If a multi-capability workflow fails partway through, what happens?

**Scenario:** User requested Databricks + OpenAI. Databricks succeeds, OpenAI fails.

**Options:**
- **A) Fail fast:** Stop, report error, leave Databricks deployed
- **B) Automatic rollback:** Destroy Databricks, restore to initial state
- **C) User choice:** Ask user "OpenAI failed. Rollback Databricks or keep it?"
- **D) Partial success:** Mark Databricks as done, allow retry of OpenAI only

**My recommendation:** Start with (D) for MVP - treat each capability as independent. Add rollback orchestration later.

**Your preference?**

---

### **Q9: Current Implementation Migration**
**Question:** How to evolve current spike code into this architecture?

**Migration path options:**

**Option A - Wrapper Approach:**
```
1. Keep current implementation as "DatabricksCapability"
2. Build orchestrator layer on top
3. Add capability registry
4. Gradually add new capabilities
```

**Option B - Refactor Approach:**
```
1. Refactor current code into WorkflowSteps
2. Build orchestrator from scratch
3. Plug in refactored steps
4. Add conversation layer
```

**Option C - Parallel Development:**
```
1. Build new architecture in separate module
2. Keep spike as reference implementation
3. Migrate pieces gradually
4. Deprecate old code when ready
```

**My recommendation:** **Option A** - least disruptive, validates platform architecture before big refactor.

**Your preference?**

---

## 4. Proposed Implementation Plan

### Phase 1: Conversational Enhancement (Current Databricks Agent)
**Goal:** Add multi-turn conversation to existing agent

**Tasks:**
- [ ] Add session state management (file-based)
- [ ] Implement clarifying question generation
- [ ] Build conversation loop in CLI
- [ ] Add smart naming suggestions with override
- [ ] Enhanced approval workflow with customization options

**Output:** Current agent becomes more user-friendly and interactive

**Duration:** 1-2 weeks

---

### Phase 2: Orchestrator Foundation
**Goal:** Build capability routing layer

**Tasks:**
- [ ] Create CapabilityRegistry class
- [ ] Build OrchestratorAgent with workflow planning
- [ ] Migrate Databricks agent to "capability" pattern
- [ ] Implement capability discovery and routing
- [ ] Add multi-capability workflow execution

**Output:** Platform can route to single capability (Databricks only for now)

**Duration:** 2-3 weeks

---

### Phase 3: Second Capability (Validation)
**Goal:** Prove platform works with multiple capabilities

**Tasks:**
- [ ] Implement "Provision OpenAI" capability
- [ ] Test orchestrator with multi-capability request
- [ ] Add capability-level state management
- [ ] Implement partial success handling

**Output:** Platform successfully orchestrates 2 capabilities

**Duration:** 2 weeks

---

### Phase 4: Production Hardening
**Goal:** Make platform production-ready

**Tasks:**
- [ ] Add comprehensive error handling
- [ ] Implement audit logging
- [ ] Add rollback capabilities
- [ ] Build monitoring and observability
- [ ] Create capability development guide

**Output:** Production-ready platform

**Duration:** 3-4 weeks

---

## 5. Open Questions for Discussion

1. **Framework Selection:** Stick with direct OpenAI API or adopt MAF/Semantic Kernel for orchestration?

2. **Clarifying Questions Depth:** Minimal, Moderate, or Comprehensive?

3. **Naming Strategy:** Auto-generate, user-provided, or smart suggestions?

4. **Capability Discovery:** Explicit, intent-based, or hybrid with confirmation?

5. **Multi-Agent vs MCP:** What's the decision criteria? Complexity? LLM requirement? Something else?

6. **State Storage:** File-based for MVP or go straight to database?

7. **Validation Gates:** Per-capability, per-plan, or hybrid approach?

8. **Error Handling:** Partial success with retry or rollback automation?

9. **Migration Path:** Wrapper, refactor, or parallel development?

10. **Timeline:** Do these phases align with Rio Tinto expectations? Any hard deadlines?

---

## 6. Technical Considerations

### Performance
- Current: 13 minutes for Databricks
- Multi-capability: Could be 20-30 minutes for multiple provisions
- Conversation overhead: Additional 2-5 minutes for Q&A

### Scalability
- Capability registry needs efficient lookup (100s of capabilities eventually?)
- State management must handle concurrent users
- LLM rate limits (multiple calls per workflow)

### Cost
- More LLM calls = higher OpenAI costs
- Multi-turn conversations increase token usage
- Consider caching common patterns

### Security
- Multi-capability workflows = broader permissions needed
- Audit trail becomes critical
- Role-based access to capabilities

---

## Next Steps

**DECISIONS MADE (Nov 6, 2025):**

### Architectural Decisions

**Q1 - Framework:** Microsoft Agent Framework (MAF) for orchestration
- Provides multi-turn conversation primitives
- Agent-to-agent communication built-in
- Flexibility to use different frameworks per capability if needed
- Good documentation available

**Q2 - Conversation Depth:** Moderate with key customizations
- Ask about: resource group name, naming conventions, budget constraints
- Keep natural conversational flow ("chatbot" style)
- Balance between control and simplicity

**Q3 - Naming Strategy:** Smart suggestions with override
- Agent suggests names based on conventions
- User can accept or customize
- Example: "rg-ml-prod" → "rg-production-ml"

**Q4 - Capability Discovery:** Hybrid (propose + confirm)
- Orchestrator proposes required capabilities
- User confirms or modifies list
- Note: May simplify for initial spike if complex

**Q5 - Multi-Agent vs MCP:** User/use-case dependent
- Databricks provisioning: Multi-agent system (current implementation)
- Decision deferred for other capabilities

**Q6 - State Management:** In-memory for spike, enhance later
- Focus on end-to-end flow first
- State persistence is important for production but deprioritized for spike
- Will add file-based or DB persistence after E2E validation

**Q7 - Validation Gates:** Hybrid (approve plan + confirm critical steps)
- Approve overall plan upfront
- Confirm before expensive/security-sensitive operations

**Q8 - Error Handling:** Partial success with retry (Option D)
- Each capability independent
- Allow retry of failed capabilities without rolling back successful ones

**Q9 - Migration Strategy:** Clean refactor with proper structure
- **CRITICAL:** Spike must be presentable to team as MVP skeleton
- Use proper framework conventions (MAF patterns)
- Clean code structure that scales to production
- Avoid "brute force" implementations

---

## Recommended Implementation Strategy

### Goal
Create a **production-quality spike** that demonstrates:
1. MAF-based orchestrator pattern
2. Multi-turn conversational flow
3. Capability-based architecture
4. Clean, scalable code structure

### Implementation Status

**✅ COMPLETED PHASES:**

**Phase 0: MAF Foundation** ✅
- Installed Microsoft Agent Framework (MAF) v2025-03-01-preview
- Validated Azure OpenAI connectivity with MAF
- Created basic orchestrator agent structure
- Implemented conversation loop

**Phase 1: Conversational Orchestrator** ✅
- Multi-turn conversation with clarifying questions
- Natural language parameter gathering
- Conversation context managed by MAF automatically

**Phase 1.5: Tool Registry Pattern** ✅
- Dynamic tool registration with decorators (`@tool_manager.register`)
- Auto-schema generation from type hints
- Four tools implemented:
  - `select_capabilities`: Validate capability names
  - `suggest_naming`: Generate Azure-compliant resource names
  - `estimate_cost`: Calculate monthly cost breakdown
  - `execute_deployment`: Trigger actual deployment

**Phase 1.6: Capability Registry** ✅
- Prevents LLM hallucination by validating capability names
- Registry of allowed infrastructure capabilities
- Semantic understanding (LLM) + validation (registry)

**Phase 2: Capability Integration** ✅
- Created BaseCapability interface (plan/execute lifecycle)
- Refactored Databricks deployment as DatabricksCapability
- Capability wraps existing agent/ modules
- Successful Azure deployment (13 minutes end-to-end)

**🎯 Current State:** Spike complete with working end-to-end deployment

---

## Key Principles for Clean Implementation

### 1. **Separation of Concerns**
```python
# Orchestrator: Understands user intent, routes to capabilities
# Capability: Knows how to provision specific infrastructure
# NOT: Orchestrator doing Terraform operations directly
```

### 2. **MAF Patterns**
```python
# Use MAF's agent decorators and conversation primitives
# Follow MAF project structure conventions
# Leverage MAF's built-in state management (even if in-memory)
```

### 3. **Interface-Based Design**
```python
class BaseCapability(ABC):
    """All capabilities implement this interface"""

    @abstractmethod
    async def plan(self, request: CapabilityRequest) -> CapabilityPlan:
        """Generate execution plan"""
        pass

    @abstractmethod
    async def execute(self, plan: CapabilityPlan) -> CapabilityResult:
        """Execute the capability"""
        pass

    @abstractmethod
    def get_clarifying_questions(self, request: CapabilityRequest) -> list[Question]:
        """Return questions to ask user"""
        pass
```

### 4. **Testability**
- Each capability independently testable
- Orchestrator testable with mock capabilities
- Clear boundaries between components

### 5. **Documentation**
- Inline docstrings (Google style)
- Architecture diagrams in `/docs`
- README with clear examples
- Demo script for team presentation

---

## Immediate Next Steps (Pending Your Approval)

**PHASE 0 APPROVED - READY TO START**

See detailed implementation plan in: `/docs/MAF_RESEARCH_AND_IMPLEMENTATION_PLAN.md`

### Summary of Decisions:
- ✅ **Framework**: Microsoft Agent Framework (MAF)
- ✅ **Orchestrator**: MAF Agent with multi-turn conversation
- ✅ **Capabilities**: BaseCapability interface, Databricks refactored as first capability
- ✅ **State**: In-memory for spike (MAF built-in context)
- ✅ **Discovery**: Hybrid (propose + confirm)
- ✅ **Conversation**: Moderate depth with smart suggestions
- ✅ **Timeline**: Phase-by-phase with validation at each step

### Immediate Actions (Next Session):

---

## Next Steps: From Spike to Production Platform

### Spike Validation Complete ✅

The spike successfully demonstrated:
- ✅ MAF-based conversational orchestration
- ✅ Tool-enabled multi-turn conversations
- ✅ Capability-based architecture pattern
- ✅ End-to-end Azure deployment (verified working)
- ✅ Clean, maintainable code structure

**Deployment Proof:**
- Workspace: `https://adb-4412170593674511.11.azuredatabricks.net`
- Resource Group: `rg-e2e-deploy-dev`
- Duration: ~13 minutes (785 seconds)

### Recommended Next Phases (Post-Spike)

#### Phase 3: State Persistence & Robustness
**Goal:** Production-grade state management and error handling

**Tasks:**
- [ ] File-based or database-backed conversation state
- [ ] Resume interrupted deployments
- [ ] Comprehensive error handling with user-friendly messages
- [ ] Rollback capability on deployment failures
- [ ] Audit logging for all operations

**Duration:** 2-3 weeks

---

#### Phase 4: Second Capability (Multi-Capability Validation)
**Goal:** Prove platform works with multiple infrastructure types

**Candidate Capabilities:**
- Azure OpenAI provisioning (LLM deployments)
- Azure Firewall port management
- Azure Storage account with access policies
- Azure ML workspace provisioning

**Tasks:**
- [ ] Implement second capability following BaseCapability interface
- [ ] Test orchestrator with multi-capability workflows
- [ ] Add capability dependency management
- [ ] Implement partial success handling

**Duration:** 2-3 weeks

---

#### Phase 5: Enterprise Features
**Goal:** Production-ready platform for team deployment

**Tasks:**
- [ ] Role-based access control (who can provision what)
- [ ] Cost budgets and approval workflows
- [ ] Monitoring and alerting integration
- [ ] Jira/ServiceNow ticket integration
- [ ] Self-service portal or Slack/Teams bot interface
- [ ] Comprehensive documentation and runbooks

**Duration:** 4-6 weeks

---

### Open Questions for Production Evolution

#### Q1: State Management Strategy
- **File-based**: Simple, works for small teams
- **Database**: Scalable, supports concurrent users, audit trail
- **Azure Storage**: Cloud-native, good for serverless deployment

**Recommendation:** Start with file-based for Phase 3, migrate to database in Phase 5

#### Q2: Approval Workflow Integration
- **Built-in**: Simple approval prompts (current spike approach)
- **External**: Jira/ServiceNow ticket creation and status polling
- **Hybrid**: Built-in for dev, external for prod deployments

**Recommendation:** Hybrid approach for flexibility

#### Q3: Multi-Capability Dependencies
**Scenario:** User needs OpenAI capability but it requires firewall rules

**Options:**
- Orchestrator automatically detects dependencies
- User explicitly requests both capabilities
- Capability can invoke other capabilities

**Recommendation:** Start with explicit requests, add dependency detection in Phase 5

#### Q4: Deployment Patterns
- **Single-tenant**: Each user gets their own orchestrator instance
- **Multi-tenant**: Shared orchestrator with session isolation
- **Serverless**: Azure Functions + durable orchestration

**Recommendation:** Single-tenant for Phase 3-4, evaluate multi-tenant for Phase 5

---

### Timeline Estimates

**Phase 3 (State + Robustness):** 2-3 weeks
**Phase 4 (Second Capability):** 2-3 weeks
**Phase 5 (Enterprise Features):** 4-6 weeks

**Total to Production:** 8-12 weeks with testing and iteration

---

### Success Metrics

**Spike (Current):** ✅ Complete
- Working deployment from conversation to infrastructure
- Clean architecture with extensibility points
- Documentation for handoff

**Phase 3:** State + Robustness
- Can resume interrupted deployments
- Error recovery without manual intervention
- Audit trail for all operations

**Phase 4:** Multi-Capability
- Successfully orchestrate 2+ different infrastructure types
- Handle inter-capability dependencies
- Partial success workflows

**Phase 5:** Enterprise Production
- 10+ capabilities available
- 50+ successful deployments
- < 5% failure rate
- User satisfaction > 4/5


