# Current Repository Structure - Visual Guide

**Last Updated**: November 7, 2025
**Status**: ✅ Spike Complete - Successful Azure deployment verified

## Directory Tree

```
agent-infra-spike/
│
├── 📂 orchestrator/                    ← MAF-based conversational orchestrator [ACTIVE]
│   ├── __init__.py                     Exports: InfrastructureOrchestrator
│   ├── orchestrator_agent.py           MAF agent with multi-turn conversation
│   │                                   - Detects execute_deployment and runs capability
│   ├── capability_registry.py          Validates capability names (anti-hallucination)
│   ├── tool_manager.py                 Dynamic tool registration with @decorator
│   │                                   - Auto-generates schemas from type hints
│   ├── tools.py                        4 tools: select_capabilities, suggest_naming,
│   │                                   estimate_cost, execute_deployment
│   └── models.py                       ConversationState, ProvisioningPlan
│
├── 📂 capabilities/                    ← Pluggable infrastructure provisioning [ACTIVE]
│   ├── __init__.py                     Exports: BaseCapability, data models
│   ├── base.py                         BaseCapability interface (plan/validate/execute/rollback)
│   │                                   CapabilityContext, CapabilityPlan, CapabilityResult
│   ├── README.md                       How to add new capabilities
│   │
│   └── 📂 databricks/                  ← Databricks workspace provisioning [WORKING]
│       ├── __init__.py                 Exports: DatabricksCapability
│       └── capability.py               Wraps agent/ modules in BaseCapability interface
│                                       - plan(): Generate deployment plan + cost estimate
│                                       - execute(): Run terraform apply, return workspace URL
│
├── 📂 agent/                           ← Databricks deployment logic [ACTIVE - NOT DEPRECATED]
│   ├── __init__.py                     Exports all modules
│   ├── infrastructure_agent.py         Legacy single-shot interface (still works)
│   ├── intent_recognizer.py            LLM: Parse NL → InfrastructureRequest
│   ├── decision_engine.py              Logic: GPU/CPU, sizing, Premium/Standard SKU
│   ├── terraform_generator.py          Jinja2: Generate HCL from decisions
│   ├── terraform_executor.py           Execute: terraform init/plan/apply
│   ├── models.py                       InfrastructureRequest, InfrastructureDecision, Result
│   └── config.py                       Azure credentials loader
│
├── 📂 templates/                       ← Terraform Jinja2 templates [ACTIVE]
│   ├── main.tf.j2                      Resource definitions (RG, Workspace, Cluster)
│   ├── variables.tf.j2                 Variable declarations
│   ├── outputs.tf.j2                   Output definitions (workspace_url, workspace_id)
│   ├── provider.tf.j2                  Azure + Databricks provider config
│   └── terraform.tfvars.j2             Variable values
│
├── 📂 terraform_workspaces/            ← Working directories for deployments
│   └── <workspace-name>_plan/          Generated per deployment
│       ├── main.tf                     (5 Terraform files written here)
│       ├── variables.tf
│       ├── outputs.tf
│       ├── provider.tf
│       ├── terraform.tfvars
│       └── terraform.tfstate           (after apply)
│
├── 📂 tests/                           ← Test suite (23 tests total)
│   ├── test_maf_setup.py               Phase 0: MAF + Azure OpenAI (6 tests) ✅
│   ├── test_orchestrator.py            Phase 1: Orchestrator + tools (9 tests) ✅
│   ├── test_capability_integration.py  Phase 2: Capability integration (8 tests) ✅
│   ├── test_*.py                       Debug/validation scripts (can be cleaned up)
│   └── test_e2e_conversation.py        E2E conversational flow test
│
├── 📂 docs/                            ← Documentation [CLEANED UP]
│   ├── PRD.md                          Product requirements and vision
│   ├── ARCHITECTURE_EVOLUTION.md       Architecture decisions, agent/ vs capabilities/
│   │                                   current state, next phases
│   ├── STRUCTURE_VISUAL_GUIDE.md       This file - structure overview
│   ├── MAF_RESEARCH_AND_IMPLEMENTATION_PLAN.md  MAF integration research
│   ├── MAF_TOOL_CALLING_FIX.md         Technical notes on fixing tool calling
│   └── implementation_status/          Phase-by-phase progress tracking
│       ├── PHASE_0_RESULTS.md
│       ├── PHASE_1_RESULTS.md
│       ├── PHASE_1.5_TOOL_REGISTRY.md
│       ├── PHASE_1.6_CAPABILITY_REGISTRY.md
│       └── PHASE_2_CAPABILITY_INTEGRATION.md
│
├── 📂 .github/
│   └── copilot-instructions.md         ← PRIMARY guidance for GitHub Copilot
│
├── cli_maf.py                          🎯 Conversational CLI [USE THIS]
│                                       - Multi-turn conversation with orchestrator
│                                       - Working deployment to Azure
├── pyproject.toml                      Python dependencies (MAF, Azure OpenAI, Terraform)
├── README.md                           Project overview
└── .env                                Azure credentials (AZURE_OPENAI_*, AZURE_SUBSCRIPTION_ID)
```

## Implementation Status

### ✅ Completed Phases

**Phase 0: MAF Integration** ✅
- Microsoft Agent Framework v2025-03-01-preview
- Azure OpenAI connectivity validated
- 6 tests passing

**Phase 1: Conversational Orchestrator** ✅
- Multi-turn conversation with parameter gathering
- MAF automatic context management
- 9 tests passing

**Phase 1.5: Tool Registry Pattern** ✅
- Dynamic tool registration with `@tool_manager.register`
- Auto-schema generation from type hints
- 4 tools: select_capabilities, suggest_naming, estimate_cost, execute_deployment

**Phase 1.6: Capability Registry** ✅
- Anti-hallucination validation
- LLM semantic understanding + registry validation
- Prevents invalid capability names

**Phase 2: Capability Integration** ✅
- BaseCapability interface (plan/validate/execute/rollback)
- DatabricksCapability wrapping agent/ modules
- Actual Azure deployment working
- 8 tests passing

### 🎉 Deployment Proof

**Successfully deployed to Azure:**
- Workspace URL: `https://adb-4412170593674511.11.azuredatabricks.net`
- Resource Group: `rg-e2e-deploy-dev`
- Subscription: Verified in Azure portal
- Duration: ~13 minutes (785 seconds)
- Resources: RG + Workspace + Cluster (GPU instances)

### 🎯 Current Scope

**Single Capability by Design:**
- Focus: Databricks provisioning (RG + Workspace + Cluster as atomic unit)
- Status: Working end-to-end from conversation → deployment
- Not adding: OpenAI, Firewall, or other capabilities (spike is complete)

---

## Data Flow

### User Request → Infrastructure Deployment

```
┌─────────────────────────────────────────────────────────────────┐
│                         USER INPUT                              │
│  "I need a Databricks workspace for ML team in production"     │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│                    CLI (cli_maf.py)                             │
│  Captures user input, calls orchestrator                        │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│              ORCHESTRATOR (orchestrator_agent.py)               │
│  ┌───────────────────────────────────────────────────────────┐ │
│  │ 1. Multi-turn conversation (MAF handles context)          │ │
│  │ 2. Uses tools to gather parameters:                       │ │
│  │    - select_capabilities (validates against registry)     │ │
│  │    - suggest_naming (Azure naming conventions)            │ │
│  │    - estimate_cost (monthly cost breakdown)               │ │
│  │    - execute_deployment (triggers actual deployment)      │ │
│  │ 3. Detects execute_deployment in response.messages        │ │
│  │ 4. Calls capability.plan() → capability.execute()         │ │
│  └───────────────────────────────────────────────────────────┘ │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│        CAPABILITY (capabilities/databricks/capability.py)       │
│  ┌───────────────────────────────────────────────────────────┐ │
│  │ plan() Phase:                                             │ │
│  │   - Build request from context.parameters                 │ │
│  │   - Call agent/intent_recognizer.py (parse to IR)         │ │
│  │   - Call agent/decision_engine.py (IR → Decision)         │ │
│  │   - Call agent/terraform_generator.py (Decision → HCL)    │ │
│  │   - Call agent/terraform_executor.py (terraform plan)     │ │
│  │   - Estimate costs from Decision                          │ │
│  │   - Store ALL 5 terraform files in plan.details           │ │
│  │   - Return CapabilityPlan with resources, costs, files    │ │
│  └───────────────────────────────────────────────────────────┘ │
│                                                                 │
│  ┌───────────────────────────────────────────────────────────┐ │
│  │ execute() Phase:                                          │ │
│  │   - Reconstruct TerraformFiles from plan.details          │ │
│  │   - Call agent/terraform_executor.py (terraform apply)    │ │
│  │   - Parse workspace URL, ID from outputs                  │ │
│  │   - Return CapabilityResult(success, outputs, duration)   │ │
│  └───────────────────────────────────────────────────────────┘ │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│           AGENT MODULES (agent/)  [ACTIVE - NOT DEPRECATED]     │
│  ┌─────────────────┬─────────────────┬─────────────────────┐   │
│  │ IntentRecognizer│  DecisionEngine │  TerraformGenerator │   │
│  │ (LLM-based)     │  (Business logic)│  (Jinja2 rendering)│   │
│  │ NL → IR         │  IR → Decision  │  Decision → HCL     │   │
│  └─────────────────┴─────────────────┴─────────────────────┘   │
│                                                                 │
│  ┌────────────────────────────────────────────────────────┐    │
│  │              TerraformExecutor                         │    │
│  │  - Write 5 Terraform files to working directory       │    │
│  │    (main.tf, variables.tf, outputs.tf,                │    │
│  │     provider.tf, terraform.tfvars)                     │    │
│  │  - Run: terraform init                                 │    │
│  │  - Run: terraform plan (dry_run=True)                  │    │
│  │       or terraform apply (dry_run=False)               │    │
│  │  - Parse outputs: workspace_url, workspace_id, etc.    │    │
│  └────────────────────────────────────────────────────────┘    │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│                    AZURE RESOURCES (Deployed) ✅                │
│  ✓ Resource Group: rg-e2e-deploy-dev                            │
│  ✓ Databricks Workspace: e2e-deploy-dev                         │
│    URL: https://adb-4412170593674511.11.azuredatabricks.net     │
│  ✓ Databricks Cluster: e2e-deploy-dev-cluster (GPU instances)   │
│  ⏱  Deployment time: ~13 minutes (785 seconds)                  │
└─────────────────────────────────────────────────────────────────┘
```

---

## Key Architectural Insights

### 1. `agent/` is ACTIVE, Not Deprecated

**Common Misconception**: "agent/ is deprecated, capabilities/ replaced it"

**Reality**: They work **together**:
- `agent/` = Actual deployment code (IntentRecognizer, DecisionEngine, TerraformGenerator, TerraformExecutor)
- `capabilities/` = Standard interface wrapper so orchestrator can call agent/ in pluggable way
- `capabilities/databricks/capability.py` imports and uses all agent/ modules

**Why?**: Orchestrator needs standard interface (plan/execute), agent/ has proven deployment logic. Capability wrapper provides the interface, agent/ does the work.

### 2. Tool Calling Fix (Critical for MAF)

**Problem**: Initial implementation passed JSON schemas to MAF, not actual functions
**Solution**: Changed to pass actual Python callables from `tool_manager.get_tool_functions()`
**Result**: MAF can now automatically invoke tools during conversation

**Key Pattern**:
```python
# ❌ OLD: Passing schemas (MAF couldn't execute)
tools = tool_manager.get_schemas(wrapped=True)

# ✅ NEW: Passing actual functions (MAF executes automatically)
tools = tool_manager.get_tool_functions()
```

### 3. Tool Parameters: Individual vs Dict

**Changed from**:
```python
def execute_deployment(deployment_details: dict) -> str:
    # LLM struggled to populate complex dict
```

**Changed to**:
```python
def execute_deployment(
    capability_name: Annotated[str, Field(description="...")],
    team: Annotated[str, Field(description="...")],
    environment: Annotated[str, Field(description="...")],
    # ... individual parameters
) -> str:
    # LLM easily fills individual parameters
```

**Why**: Individual typed parameters with Field descriptions give LLM clear structure

### 4. Deployment Detection Pattern

**How orchestrator knows to actually deploy**:
```python
# In orchestrator_agent.py::process_message()
for msg in response.messages:
    if hasattr(msg, "tool_calls") and msg.tool_calls:
        for tool_call in msg.tool_calls:
            if tool_call.name == "execute_deployment":
                # Extract parameters from tool_call.arguments
                # Create CapabilityContext
                # Call capability.plan() then capability.execute()
                # This is ACTUAL deployment, not queued!
```

### 5. Terraform File Persistence

**Critical bug fixed**: Must store ALL 5 terraform files in plan

**Files required**:
1. `main.tf` - Resource definitions
2. `variables.tf` - Variable declarations
3. `outputs.tf` - Output definitions
4. `provider.tf` - Provider configuration (Azure, Databricks)
5. `terraform.tfvars` - Variable values

**Why**: `execute()` reconstructs `TerraformFiles` from `plan.details["terraform_files"]`. Missing files caused 'NoneType' errors.

---

## Import Graph

### How Modules Depend on Each Other

```
┌─────────────────────────────────────────────────────────────────┐
│                        USER SPACE                               │
│                                                                 │
│  cli_maf.py  ──────────┐  (Multi-turn conversation)            │
│                        │                                        │
└────────────────────────┼────────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────┼───────────────────────┐
│                   ORCHESTRATOR LAYER    │                       │
│                                         │                       │
│  orchestrator/orchestrator_agent.py  ◄──┘                       │
│      ↓                       ↓                                  │
│  orchestrator/         orchestrator/                            │
│  tool_manager.py       capability_registry.py                   │
│      ↓                                                          │
│  orchestrator/tools.py                                          │
│      ↓                                                          │
└─────┼───────────────────────────────────────────────────────────┘
      │
      ▼
┌─────────────────────────────────────────────────────────────────┐
│                   CAPABILITY LAYER                              │
│                                                                 │
│  capabilities/__init__.py  (exports BaseCapability, models)     │
│      ↓                                                          │
│  capabilities/base.py  (BaseCapability interface)               │
│                        (CapabilityContext, Plan, Result)        │
│                                                                 │
│  capabilities/databricks/__init__.py                            │
│      ↓                                                          │
│  capabilities/databricks/capability.py                          │
│      ↓ (imports agent modules)                                 │
└─────┼───────────────────────────────────────────────────────────┘
      │
      ▼
┌─────────────────────────────────────────────────────────────────┐
│                    AGENT LAYER (Active Deployment Code)         │
│                                                                 │
│  agent/__init__.py  (exports all modules)                       │
│      ↓                                                          │
│  agent/intent_recognizer.py    (LLM: NL → InfrastructureRequest)│
│  agent/decision_engine.py      (Logic: IR → Decision)           │
│  agent/terraform_generator.py  (Jinja2: Decision → HCL)         │
│  agent/terraform_executor.py   (Terraform CLI: HCL → Azure)     │
│  agent/models.py                (Data models)                   │
│  agent/config.py                (Azure credentials)             │
└─────────────────────────────────────────────────────────────────┘
```

## Key Files by Purpose

### 🎯 Entry Point
- **`cli_maf.py`** - **USE THIS** - Conversational interface with actual deployment

### Orchestration (Phase 1 + 1.5 + 1.6)
- **`orchestrator/orchestrator_agent.py`** - Main MAF agent, conversation management
- **`orchestrator/tool_manager.py`** - Tool registry with @decorator pattern
- **`orchestrator/tools.py`** - 4 tool implementations (select, suggest, estimate, execute)
- **`orchestrator/capability_registry.py`** - Anti-hallucination validation
- `orchestrator/models.py` - ConversationState, ProvisioningPlan, PlanStep

### Capability System (Phase 2)
- **`capabilities/base.py`** - BaseCapability interface (plan/validate/execute/rollback)
- **`capabilities/databricks/capability.py`** - DatabricksCapability implementation
- `capabilities/README.md` - How to add new capabilities
- `capabilities/__init__.py` - Exports BaseCapability, CapabilityContext/Plan/Result

### Agent Deployment Code (Active - Not Deprecated)
- **`agent/intent_recognizer.py`** - LLM-based NL parsing to InfrastructureRequest
- **`agent/decision_engine.py`** - Configuration decision logic (GPU/CPU, sizing, SKU)
- **`agent/terraform_generator.py`** - Jinja2 template rendering (Decision → HCL)
- **`agent/terraform_executor.py`** - Terraform CLI wrapper (init/plan/apply)
- `agent/infrastructure_agent.py` - Original single-shot agent interface
- `agent/models.py` - InfrastructureRequest, InfrastructureDecision, DeploymentResult
- `agent/config.py` - Azure config loader (credentials, subscription)

### Configuration & Templates
- **`.env`** - Azure credentials (AZURE_OPENAI_*, AZURE_SUBSCRIPTION_ID, AZURE_TENANT_ID)
- **`templates/*.tf.j2`** - 5 Terraform Jinja2 templates (main, variables, outputs, provider, tfvars)
- `pyproject.toml` - Python dependencies and project metadata

### Testing (23 tests total, all passing ✅)
- **`tests/test_maf_setup.py`** - Phase 0: MAF + Azure OpenAI validation (6 tests)
- **`tests/test_orchestrator.py`** - Phase 1: Orchestrator + tools (9 tests)
- **`tests/test_capability_integration.py`** - Phase 2: Capability integration (8 tests)
- `tests/test_e2e_conversation.py` - E2E conversational flow
- `tests/test_*.py` - Debug/validation scripts (can be cleaned up)

### Documentation
- **`.github/copilot-instructions.md`** - **PRIMARY** guidance for GitHub Copilot
- **`docs/ARCHITECTURE_EVOLUTION.md`** - Architecture vision, decisions, agent/ vs capabilities/
- **`docs/STRUCTURE_VISUAL_GUIDE.md`** - This file - structure overview
- `docs/PRD.md` - Product requirements and original vision
- `docs/MAF_RESEARCH_AND_IMPLEMENTATION_PLAN.md` - MAF integration research
- `docs/MAF_TOOL_CALLING_FIX.md` - Technical notes on fixing tool calling
- `docs/implementation_status/PHASE_*.md` - Phase-by-phase progress

## Adding a New Capability

### Prerequisites
1. Understand BaseCapability interface in `capabilities/base.py`
2. Review working example: `capabilities/databricks/`
3. Read capability development guide: `capabilities/README.md`

### File Creation Steps

```
1. Create directory:
   capabilities/<capability-name>/

   Example: capabilities/openai/ for Azure OpenAI provisioning

2. Create capability implementation:
   capabilities/<capability-name>/capability.py

   class MyCapability(BaseCapability):
       @property
       def name(self) -> str:
           return "provision_<resource>"

       @property
       def description(self) -> str:
           return "Provision <resource> in Azure"

       async def plan(self, context: CapabilityContext) -> CapabilityPlan:
           """Generate deployment plan (dry-run)"""
           # Parse context.parameters
           # Make configuration decisions
           # Generate infrastructure code (Terraform/ARM/Bicep)
           # Estimate costs
           # Return CapabilityPlan

       async def execute(self, plan: CapabilityPlan) -> CapabilityResult:
           """Execute approved plan"""
           # Deploy infrastructure
           # Parse outputs
           # Return CapabilityResult

3. Create __init__.py:
   capabilities/<capability-name>/__init__.py

   from .capability import MyCapability

   __all__ = ["MyCapability"]

4. Register in orchestrator:
   orchestrator/orchestrator_agent.py

   In _register_capabilities() method:
       from capabilities.<capability-name> import MyCapability
       self.capabilities["provision_<resource>"] = MyCapability()

5. Register in capability registry:
   orchestrator/capability_registry.py

   capability_registry.register(
       name="provision_<resource>",
       description="Provision <resource> infrastructure",
       tags=["azure", "<category>"],
       required_params=["param1", "param2"],
       optional_params=["param3"]
   )

6. Create tests:
   tests/test_<capability-name>_integration.py

   Test plan() and execute() methods
   Mock external calls (Azure, Terraform)
   Verify CapabilityPlan and CapabilityResult structure

7. Update documentation:
   - Add to capabilities/README.md (list of capabilities)
   - Update this file (STRUCTURE_VISUAL_GUIDE.md)
   - Document in docs/ARCHITECTURE_EVOLUTION.md if significant
```

### What BaseCapability Provides

**Required Methods**:
- `name` (property) - Unique capability identifier
- `description` (property) - Human-readable description
- `plan(context)` - Generate deployment plan without executing
- `execute(plan)` - Execute the deployment

**Optional Methods**:
- `validate(context)` - Pre-flight validation checks
- `rollback(context, error)` - Cleanup on failure

**Data Models**:
- `CapabilityContext` - Input parameters from orchestrator
- `CapabilityPlan` - Deployment plan (resources, costs, details)
- `CapabilityResult` - Execution result (success, outputs, duration)

### Reference Implementations
- **Working**: `capabilities/databricks/` - Complete Databricks provisioning
- **Example**: See `capabilities/README.md` for more patterns

---

## Quick Start

### Run the Conversational Interface

```bash
# Ensure .env has Azure credentials
cd /workspaces/agent-infra-spike
python cli_maf.py

# Example interaction:
# You: "I need a Databricks workspace for ML experimentation"
# Agent: [asks clarifying questions about team, environment, region]
# Agent: [proposes deployment plan with costs]
# Agent: [executes deployment to Azure]
# Result: Working Databricks workspace in ~13 minutes
```

### Run Tests

```bash
# All tests (23 tests)
pytest tests/ -v

# By phase
pytest tests/test_maf_setup.py -v              # Phase 0 (6 tests)
pytest tests/test_orchestrator.py -v           # Phase 1 (9 tests)
pytest tests/test_capability_integration.py -v # Phase 2 (8 tests)

# With coverage
pytest tests/ --cov=orchestrator --cov=capabilities --cov=agent
```

### Project Status

**✅ Spike Complete**: All phases implemented, deployment verified
**🎯 Next**: See `docs/ARCHITECTURE_EVOLUTION.md` for post-spike roadmap (Phase 3-5)

---

**This structure is the source of truth.**

- For coding guidance: See `.github/copilot-instructions.md`
- For architecture decisions: See `docs/ARCHITECTURE_EVOLUTION.md`
- For capability development: See `capabilities/README.md`
- For implementation progress: See `docs/implementation_status/PHASE_*.md`

**Last Updated**: November 7, 2025
