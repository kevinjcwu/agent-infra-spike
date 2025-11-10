# Repository Structure - Visual Guide

**Last Updated**: November 10, 2025
**Status**: ✅ Current Architecture (Post-Refactoring)

This guide shows the actual current structure after the November 10, 2025 refactoring.

---

## 📁 Repository Overview

```
agent-infra-spike/
│
├── 📂 orchestrator/                    # MAF-based conversational orchestrator
│   ├── __init__.py
│   ├── orchestrator_agent.py           # Multi-turn conversation manager
│   ├── tool_manager.py                 # Dynamic tool registration (@decorator pattern)
│   ├── capability_registry.py          # Anti-hallucination validation
│   ├── tools.py                        # 4 tools: select, suggest, estimate, execute
│   └── models.py                       # ConversationState, ProvisioningPlan
│
├── 📂 capabilities/                    # Pluggable infrastructure capabilities
│   ├── __init__.py
│   ├── base.py                         # BaseCapability interface
│   ├── README.md                       # How to add new capabilities
│   │
│   └── 📂 databricks/                  # ⭐ Databricks capability (3-layer architecture)
│       ├── __init__.py                 # Public API exports
│       ├── capability.py               # Main DatabricksCapability class
│       ├── README.md                   # Databricks capability documentation
│       │
│       ├── 📂 core/                    # 🔵 Business Logic Layer
│       │   ├── __init__.py
│       │   ├── config.py               # Databricks config (instance types, pricing)
│       │   ├── intent_parser.py        # NL → InfrastructureRequest (Azure OpenAI)
│       │   └── decision_maker.py       # Configuration decisions (GPU/CPU, SKU)
│       │
│       ├── 📂 models/                  # 🟢 Data Models Layer
│       │   ├── __init__.py
│       │   └── schemas.py              # Pydantic models (Request, Decision, Result)
│       │
│       └── 📂 provisioning/            # 🟡 Infrastructure Layer
│           ├── __init__.py
│           └── 📂 terraform/
│               ├── __init__.py
│               ├── generator.py        # Terraform HCL generation (Jinja2)
│               └── executor.py         # Terraform execution (subprocess)
│
├── 📂 templates/                       # Terraform Jinja2 templates
│   ├── main.tf.j2                      # Resource definitions
│   ├── variables.tf.j2                 # Variable declarations
│   ├── outputs.tf.j2                   # Output definitions
│   ├── provider.tf.j2                  # Provider config
│   └── terraform.tfvars.j2             # Variable values
│
├── 📂 tests/                           # Test suite (94 tests)
│   ├── test_maf_setup.py               # MAF integration tests
│   ├── test_orchestrator.py            # Orchestrator tests
│   ├── test_capability_integration.py  # End-to-end capability tests
│   ├── test_config.py                  # Config tests
│   ├── test_decision_maker.py          # Decision making tests
│   ├── test_models.py                  # Data model tests
│   ├── test_terraform_generator.py     # Terraform generation tests
│   └── test_terraform_executor.py      # Terraform execution tests
│
├── 📂 docs/                            # Documentation
│   ├── PRD.md                          # Product requirements
│   ├── ARCHITECTURE_EVOLUTION.md       # Design decisions & roadmap
│   ├── DATABRICKS_REFACTORING_SUMMARY.md  # Current refactoring details
│   ├── MAF_RESEARCH_AND_IMPLEMENTATION_PLAN.md  # MAF integration
│   ├── MAF_TOOL_CALLING_FIX.md         # Technical fix documentation
│   ├── visual_structure.md             # This file
│   └── 📂 implementation_status/       # Phase-by-phase history
│       ├── README.md
│       ├── PHASE_0_RESULTS.md
│       ├── PHASE_1_RESULTS.md
│       ├── PHASE_1.5_TOOL_REGISTRY.md
│       ├── PHASE_1.6_CAPABILITY_REGISTRY.md
│       └── PHASE_2_CAPABILITY_INTEGRATION.md
│
├── 📂 .github/
│   └── copilot-instructions.md         # ⭐ Primary coding guidelines
│
├── cli_maf.py                          # 🎯 Conversational CLI (main entry point)
├── README.md                           # Project overview
├── CURRENT_STATE.md                    # Current project status
├── pyproject.toml                      # Dependencies
└── .env                                # Azure credentials (not in git)
```

---

## 🏗️ Three-Layer Architecture (Databricks Capability)

### 🔵 Core Layer (`capabilities/databricks/core/`)
**Purpose**: Business logic and decision-making

**Files**:
- **`config.py`** - Databricks configuration
  - Instance type definitions (CPU: ds4_v2, ds5_v2 / GPU: nc6s_v3, nc12s_v3)
  - Pricing data ($0.20-3.06/hour)
  - Azure region mappings
  - Spark versions, workload size mappings

- **`intent_parser.py`** - Natural language parsing
  - Uses Azure OpenAI GPT-4o with function calling
  - Extracts: team, environment, region, workload_type
  - Returns: `InfrastructureRequest` (Pydantic model)

- **`decision_maker.py`** - Infrastructure decisions
  - Selects instance types based on workload
  - Chooses Databricks SKU (Trial/Standard/Premium)
  - Calculates costs and enforces limits
  - Returns: `InfrastructureDecision` (Pydantic model)

**No IaC coupling** - Can switch from Terraform to Bicep without touching this layer

### 🟢 Models Layer (`capabilities/databricks/models/`)
**Purpose**: Type-safe data structures

**Files**:
- **`schemas.py`** - All Pydantic data classes
  - `InfrastructureRequest` - User requirements
  - `InfrastructureDecision` - Selected configuration + costs
  - `TerraformFiles` - Generated HCL files
  - `DeploymentResult` - Deployment outputs + metadata

**Pure data** - No business logic, no external dependencies (except Pydantic)

### 🟡 Provisioning Layer (`capabilities/databricks/provisioning/terraform/`)
**Purpose**: Infrastructure-as-Code implementation

**Files**:
- **`generator.py`** - Terraform HCL generation
  - Renders Jinja2 templates from `templates/*.tf.j2`
  - Produces 5 files: main.tf, variables.tf, outputs.tf, provider.tf, terraform.tfvars

- **`executor.py`** - Terraform execution
  - Runs: `terraform init`, `plan`, `apply`, `destroy`
  - Parses JSON outputs
  - Manages working directory and state

**IaC-specific** - Could have sibling `provisioning/bicep/` in future

---

## 🔄 Data Flow

### User Request → Deployed Infrastructure

```
┌──────────────────────────────────────────────────────────────┐
│  USER: "I need Databricks for ML team in production"        │
└────────────────────────┬─────────────────────────────────────┘
                         │
                         ▼
┌──────────────────────────────────────────────────────────────┐
│  CLI (cli_maf.py)                                            │
│  • Captures user input                                       │
│  • Calls orchestrator.process_message()                      │
└────────────────────────┬─────────────────────────────────────┘
                         │
                         ▼
┌──────────────────────────────────────────────────────────────┐
│  ORCHESTRATOR (orchestrator/orchestrator_agent.py)           │
│  • Multi-turn conversation (MAF manages context)             │
│  • Uses tools:                                               │
│    - select_capabilities (validates capability names)        │
│    - suggest_naming (Azure naming conventions)               │
│    - estimate_cost (monthly cost breakdown)                  │
│    - execute_deployment (triggers deployment)                │
│  • Detects execute_deployment in LLM response                │
│  • Calls: capability.plan() → capability.execute()           │
└────────────────────────┬─────────────────────────────────────┘
                         │
                         ▼
┌──────────────────────────────────────────────────────────────┐
│  CAPABILITY (capabilities/databricks/capability.py)          │
│                                                              │
│  plan() Phase:                                               │
│    1. Parse parameters from context                          │
│    2. IntentParser: NL → InfrastructureRequest               │
│    3. DecisionMaker: Request → InfrastructureDecision        │
│    4. TerraformGenerator: Decision → TerraformFiles          │
│    5. TerraformExecutor: Run terraform plan (dry-run)        │
│    6. Return CapabilityPlan (resources, costs, files)        │
│                                                              │
│  execute() Phase:                                            │
│    1. Reconstruct TerraformFiles from plan                   │
│    2. TerraformExecutor: Run terraform apply                 │
│    3. Parse outputs (workspace_url, workspace_id)            │
│    4. Return CapabilityResult                                │
└────────────────────────┬─────────────────────────────────────┘
                         │
                         ▼
┌──────────────────────────────────────────────────────────────┐
│  AZURE RESOURCES (Deployed via Terraform)                    │
│  • Resource Group: rg-ml-team-prod                           │
│  • Databricks Workspace: ml-prod                             │
│    URL: https://adb-xxxx.azuredatabricks.net                 │
│  • Databricks Cluster: ml-prod-cluster (GPU/CPU instances)   │
└──────────────────────────────────────────────────────────────┘
```

---

## 🔧 Key Technologies

| Component | Technology | Purpose |
|-----------|-----------|---------|
| **Agent Framework** | Microsoft Agent Framework (MAF) 1.0.0b251105 | Conversation management |
| **LLM** | Azure OpenAI GPT-4o | Intent parsing, function calling |
| **Data Validation** | Pydantic 2.5+ | Type-safe data models |
| **Templating** | Jinja2 | Terraform HCL generation |
| **IaC** | Terraform 1.5+ | Infrastructure provisioning |
| **Cloud Providers** | azurerm ~3.80, databricks ~1.29 | Azure + Databricks resources |
| **Testing** | pytest + pytest-asyncio | Test suite (94 tests) |

---

## 📊 Implementation Status

### ✅ Completed Phases

**Phase 0**: MAF Integration (6 tests)
- Microsoft Agent Framework setup
- Azure OpenAI connectivity

**Phase 1**: Conversational Orchestrator (9 tests)
- Multi-turn conversation
- Parameter gathering

**Phase 1.5**: Tool Registry Pattern
- Dynamic tool registration
- Auto-schema generation

**Phase 1.6**: Capability Registry
- Anti-hallucination validation
- Capability name validation

**Phase 2**: Capability Integration (8 tests)
- BaseCapability interface
- DatabricksCapability with 3-layer architecture

**November 10 Refactoring**: Architecture cleanup
- Removed legacy agent/ directory (741 lines)
- Organized databricks into 3 layers
- Renamed classes for clarity (IntentParser, DecisionMaker)
- All 94 tests passing

### 🚀 What Works Today

✅ **Conversational Interface**: Multi-turn dialogue with parameter gathering
✅ **Tool-Enabled**: 4 working tools for capability discovery, naming, cost estimation, execution
✅ **Actual Deployment**: Deploys to Azure in ~13 minutes
✅ **Verified**: Working Databricks workspace URL in production
✅ **Test Coverage**: 94/94 tests passing (100%)

### 🎯 Future Phases (Post-Spike)

**Phase 3**: State Persistence & Robustness
- Persistent conversation state
- Resume interrupted deployments
- Comprehensive error handling

**Phase 4**: Second Capability
- Azure OpenAI provisioning
- Multi-capability workflows

**Phase 5**: Enterprise Features
- RBAC, cost budgets, approval workflows
- Monitoring, alerting, integrations

---

## 📝 Key Patterns

### 1. Tool Registry Pattern
Dynamic tool registration with decorators:
```python
@tool_manager.register("Tool description")
def my_tool(param: str) -> str:
    return result
```
- Auto-generates OpenAI function schemas
- Scales to 100+ tools without code changes

### 2. Capability Registry Pattern
Prevents LLM hallucination:
```python
capability_registry.register(
    name="provision_databricks",
    description="Provision Databricks workspace",
    tags=["azure", "databricks"]
)
```
- LLM provides semantic understanding
- Registry validates capability names
- Rejects hallucinated capabilities

### 3. Three-Layer Architecture
Clear separation of concerns:
- **Core**: What decisions do we make?
- **Models**: What data do we work with?
- **Provisioning**: How do we deploy it?

### 4. Public API Pattern
All exports through `__init__.py`:
```python
from capabilities.databricks import (
    DatabricksCapability,
    IntentParser,
    DecisionMaker,
    Config
)
```

---

## 🧪 Testing

### Test Organization
```
tests/
├── test_maf_setup.py              # 6 tests - MAF integration
├── test_orchestrator.py           # 9 tests - Orchestrator logic
├── test_capability_integration.py # 8 tests - End-to-end capability
├── test_config.py                 # 12 tests - Configuration
├── test_decision_maker.py         # 11 tests - Decision logic
├── test_models.py                 # 9 tests - Data models
├── test_terraform_generator.py    # 21 tests - HCL generation
└── test_terraform_executor.py     # 18 tests - Terraform execution
```

### Run Tests
```bash
# All tests
pytest tests/ -v

# Specific layer
pytest tests/test_decision_maker.py -v

# With coverage
pytest tests/ --cov=orchestrator --cov=capabilities
```

**Current Status**: 94/94 tests passing ✅

---

## 🎓 Learning Resources

### For New Contributors

**Start Here**:
1. `README.md` - Project overview
2. `.github/copilot-instructions.md` - Coding guidelines (PRIMARY)
3. This file - Structure understanding
4. `capabilities/databricks/README.md` - Example capability

**Deep Dives**:
- `docs/PRD.md` - Original requirements
- `docs/ARCHITECTURE_EVOLUTION.md` - Design decisions & roadmap
- `docs/DATABRICKS_REFACTORING_SUMMARY.md` - Recent refactoring details
- `docs/MAF_TOOL_CALLING_FIX.md` - Technical insights

**Adding Features**:
- `capabilities/README.md` - How to add new capabilities
- `docs/implementation_status/` - Phase-by-phase history

---

## 💡 Design Principles

### Separation of Concerns
Each module has a single responsibility - orchestrator routes, capabilities provision, layers separate business logic from infrastructure code.

### Scalability
- Tool Registry: Add tools without touching routing code
- Capability Registry: Validate capabilities without hardcoding
- Three-Layer Architecture: Template for all future capabilities

### Type Safety
Pydantic models throughout for validation and IDE support.

### Testability
Each layer independently testable with clear interfaces.

### No Premature Extraction
Keep code in capabilities until duplication appears across 2-3 capabilities, then extract to `shared/`.

---

## 📍 Entry Points

**Main CLI**: `cli_maf.py` - Conversational interface

**Key Classes**:
- `orchestrator.InfrastructureOrchestrator` - Main orchestrator
- `capabilities.databricks.DatabricksCapability` - Databricks provisioning
- `capabilities.base.BaseCapability` - Capability interface

**Configuration**: `.env` file with Azure credentials

---

**Last Updated**: November 10, 2025
**Maintainer**: GitHub Copilot + Human
**Status**: ✅ Production-ready architecture with 94/94 tests passing
