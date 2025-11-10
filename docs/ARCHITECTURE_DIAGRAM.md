# Infrastructure Orchestrator - Architecture Diagram

**Last Updated**: November 10, 2025

---

## 🎯 High-Level Architecture

```
┌─────────────────────────────────────────────────────────────────────────┐
│                          USER INTERACTION                                │
│                   "I need Databricks for ML team"                        │
└────────────────────────────────┬────────────────────────────────────────┘
                                 │
                                 ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                         CLI Interface                                    │
│                         (cli_maf.py)                                     │
│  • Interactive conversational interface                                  │
│  • Captures user requests                                                │
└────────────────────────────────┬────────────────────────────────────────┘
                                 │
                                 ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                    ORCHESTRATOR LAYER                                    │
│              (Microsoft Agent Framework + Azure OpenAI)                  │
│                                                                          │
│  ┌────────────────────────────────────────────────────────────────┐    │
│  │  OrchestratorAgent                                              │    │
│  │  • Multi-turn conversation management                           │    │
│  │  • Context retention (MAF automatic)                            │    │
│  │  • LLM-powered intent understanding                             │    │
│  └────────────────────────────────────────────────────────────────┘    │
│                                                                          │
│  ┌────────────────────────────────────────────────────────────────┐    │
│  │  Tool Manager (Dynamic Registration)                            │    │
│  │                                                                  │    │
│  │  🔧 select_capabilities  → Validate capability names            │    │
│  │  🔧 suggest_naming       → Generate Azure naming conventions    │    │
│  │  🔧 estimate_cost        → Calculate monthly costs              │    │
│  │  🔧 execute_deployment   → Trigger infrastructure provisioning  │    │
│  └────────────────────────────────────────────────────────────────┘    │
│                                                                          │
│  ┌────────────────────────────────────────────────────────────────┐    │
│  │  Capability Registry (Anti-Hallucination)                       │    │
│  │  • Validates capability names against registry                  │    │
│  │  • Prevents LLM from inventing non-existent capabilities        │    │
│  └────────────────────────────────────────────────────────────────┘    │
└────────────────────────────────┬────────────────────────────────────────┘
                                 │
                                 ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                      CAPABILITY LAYER                                    │
│                   (Pluggable Infrastructure Modules)                     │
│                                                                          │
│  ┌──────────────────────┐  ┌──────────────────────┐                    │
│  │  DatabricksCapability │  │  Future Capabilities │                    │
│  │  (Production Ready)   │  │  (Azure OpenAI, AKS) │                    │
│  └──────────┬───────────┘  └──────────────────────┘                    │
│             │                                                            │
│             │  Three-Layer Architecture:                                │
│             │                                                            │
│  ┌──────────▼──────────────────────────────────────────────────────┐   │
│  │  🔵 CORE LAYER (Business Logic)                                  │   │
│  │  • IntentParser    → NL to structured requirements               │   │
│  │  • DecisionMaker   → Select configs, calculate costs             │   │
│  │  • Config          → Instance types, pricing, regions            │   │
│  └──────────────────────────────────────────────────────────────────┘   │
│                                                                          │
│  ┌──────────────────────────────────────────────────────────────────┐   │
│  │  🟢 MODELS LAYER (Data Structures)                               │   │
│  │  • InfrastructureRequest  → User requirements                    │   │
│  │  • InfrastructureDecision → Selected configuration               │   │
│  │  • DeploymentResult       → Deployed resource outputs            │   │
│  └──────────────────────────────────────────────────────────────────┘   │
│                                                                          │
│  ┌──────────────────────────────────────────────────────────────────┐   │
│  │  🟡 PROVISIONING LAYER (Infrastructure-as-Code)                  │   │
│  │  • TerraformGenerator  → Jinja2 templates to HCL                 │   │
│  │  • TerraformExecutor   → Run terraform init/plan/apply           │   │
│  └──────────────────────────────────────────────────────────────────┘   │
└────────────────────────────────┬────────────────────────────────────────┘
                                 │
                                 ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                        AZURE CLOUD                                       │
│                                                                          │
│  ✅ Resource Group: rg-ml-team-prod                                      │
│  ✅ Databricks Workspace: ml-prod                                        │
│  ✅ Databricks Cluster: ml-prod-cluster                                  │
│  ✅ Storage Account: dbstorage                                           │
│                                                                          │
│  📊 Deployed Resources with:                                             │
│  • Workspace URL                                                         │
│  • Access credentials                                                    │
│  • Monitoring enabled                                                    │
└─────────────────────────────────────────────────────────────────────────┘
```

---

## 🔄 Request Flow (Step-by-Step)

```
┏━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┓
┃  PHASE 1: User Request & Intent Understanding                          ┃
┗━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┛

User Input
  │
  ├─▶ "I need Databricks for ML team in production"
  │
  ▼
OrchestratorAgent (Azure OpenAI GPT-4o)
  │
  ├─▶ Understands: Team=ML, Environment=Prod, Capability=Databricks
  │
  └─▶ Calls Tool: select_capabilities(["provision_databricks"])
          │
          └─▶ CapabilityRegistry validates → ✅ Valid

┏━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┓
┃  PHASE 2: Parameter Gathering (Multi-turn Conversation)               ┃
┗━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┛

OrchestratorAgent asks clarifying questions:
  │
  ├─▶ "What Azure region?" → User: "East US"
  ├─▶ "Standard or Premium tier?" → User: "Premium"
  └─▶ "GPU or CPU workload?" → User: "GPU for ML"

┏━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┓
┃  PHASE 3: Planning & Cost Estimation                                   ┃
┗━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┛

OrchestratorAgent calls tools:
  │
  ├─▶ suggest_naming(team="ML", env="prod", type="databricks")
  │     └─▶ Returns: "ml-prod", alternatives: ["dbw-ml-prod", ...]
  │
  └─▶ estimate_cost(capability="provision_databricks", parameters={...})
        └─▶ Returns: $1,200/month breakdown
              • Workspace: $0
              • GPU Cluster (NC6s_v3): $1,150
              • Storage (1TB): $50

┏━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┓
┃  PHASE 4: User Approval                                                ┃
┗━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┛

OrchestratorAgent presents plan:
  │
  ├─▶ "📋 Deployment Plan:
  │    • Name: ml-prod
  │    • Region: East US
  │    • Tier: Premium (GPU: NC6s_v3)
  │    • Cost: $1,200/month
  │
  │    Proceed? (yes/no)"
  │
  └─▶ User: "yes, deploy"

┏━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┓
┃  PHASE 5: Capability Execution                                         ┃
┗━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┛

OrchestratorAgent → execute_deployment tool
  │
  └─▶ DatabricksCapability.plan()
        │
        ├─▶ IntentParser (Azure OpenAI)
        │     └─▶ NL parameters → InfrastructureRequest
        │
        ├─▶ DecisionMaker
        │     ├─▶ Select instance type: NC6s_v3 (GPU)
        │     ├─▶ Select SKU: Premium
        │     └─▶ Calculate costs: $1,200/month
        │
        └─▶ TerraformGenerator
              ├─▶ Render main.tf (workspace + cluster)
              ├─▶ Render variables.tf
              ├─▶ Render outputs.tf
              └─▶ Run terraform plan → Preview changes

  User reviews plan → Approves

  └─▶ DatabricksCapability.execute()
        │
        └─▶ TerraformExecutor
              ├─▶ terraform init
              ├─▶ terraform apply -auto-approve
              └─▶ Parse outputs:
                    • workspace_url: https://adb-xxxx.azuredatabricks.net
                    • workspace_id: xxxxx
                    • resource_group: rg-ml-team-prod

┏━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┓
┃  PHASE 6: Completion                                                   ┃
┗━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┛

OrchestratorAgent returns to user:
  │
  └─▶ "✅ Deployment Complete!

       🎯 Your Databricks workspace is ready:
       • URL: https://adb-xxxxx.azuredatabricks.net
       • Region: East US
       • Tier: Premium (GPU-enabled)
       • Duration: 13 minutes

       Next steps:
       1. Log in to your workspace
       2. Create notebooks
       3. Start your ML experiments!"
```

---

## 🏗️ Three-Layer Capability Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                    DATABRICKS CAPABILITY                         │
│                                                                  │
│  ┏━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┓  │
│  ┃  🔵 CORE LAYER - Business Logic                         ┃  │
│  ┣━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┫  │
│  ┃                                                          ┃  │
│  ┃  📄 config.py                                            ┃  │
│  ┃    • Instance types (ds4_v2, nc6s_v3, etc.)             ┃  │
│  ┃    • Pricing data ($0.20 - $3.06/hour)                  ┃  │
│  ┃    • Azure regions                                       ┃  │
│  ┃    • Workload type mappings                              ┃  │
│  ┃                                                          ┃  │
│  ┃  🤖 intent_parser.py                                     ┃  │
│  ┃    • Uses Azure OpenAI GPT-4o                            ┃  │
│  ┃    • NL text → InfrastructureRequest                     ┃  │
│  ┃    • Extracts: team, env, region, workload              ┃  │
│  ┃                                                          ┃  │
│  ┃  🧠 decision_maker.py                                    ┃  │
│  ┃    • Request → InfrastructureDecision                    ┃  │
│  ┃    • Selects instance types (GPU vs CPU)                ┃  │
│  ┃    • Chooses SKU (Trial/Standard/Premium)               ┃  │
│  ┃    • Calculates costs & enforces limits                 ┃  │
│  ┃                                                          ┃  │
│  ┗━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┛  │
│                          ⬇                                       │
│  ┏━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┓  │
│  ┃  🟢 MODELS LAYER - Data Structures                      ┃  │
│  ┣━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┫  │
│  ┃                                                          ┃  │
│  ┃  📦 schemas.py (Pydantic models)                         ┃  │
│  ┃    • InfrastructureRequest   → User requirements        ┃  │
│  ┃    • InfrastructureDecision  → Selected config + costs  ┃  │
│  ┃    • TerraformFiles          → Generated HCL files      ┃  │
│  ┃    • DeploymentResult        → Outputs + metadata       ┃  │
│  ┃                                                          ┃  │
│  ┃  ✅ Type safety, validation, IDE support                ┃  │
│  ┃  ✅ No business logic, pure data                        ┃  │
│  ┃                                                          ┃  │
│  ┗━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┛  │
│                          ⬇                                       │
│  ┏━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┓  │
│  ┃  🟡 PROVISIONING LAYER - Infrastructure-as-Code         ┃  │
│  ┣━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┫  │
│  ┃                                                          ┃  │
│  ┃  🏗️ terraform/generator.py                              ┃  │
│  ┃    • Loads Jinja2 templates (*.tf.j2)                   ┃  │
│  ┃    • Renders with InfrastructureDecision                ┃  │
│  ┃    • Generates 5 files:                                 ┃  │
│  ┃      - main.tf (resources)                              ┃  │
│  ┃      - variables.tf (inputs)                            ┃  │
│  ┃      - outputs.tf (outputs)                             ┃  │
│  ┃      - provider.tf (providers)                          ┃  │
│  ┃      - terraform.tfvars (values)                        ┃  │
│  ┃                                                          ┃  │
│  ┃  ⚙️ terraform/executor.py                               ┃  │
│  ┃    • terraform init                                      ┃  │
│  ┃    • terraform plan (dry-run preview)                   ┃  │
│  ┃    • terraform apply (actual deployment)                ┃  │
│  ┃    • terraform destroy (cleanup)                        ┃  │
│  ┃    • Parses JSON outputs                                ┃  │
│  ┃                                                          ┃  │
│  ┗━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┛  │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

**Benefits of This Architecture**:
- ✅ **Separation of Concerns**: Each layer has single responsibility
- ✅ **IaC Agnostic**: Core layer doesn't know about Terraform (could switch to Bicep)
- ✅ **Testability**: Each layer tested independently
- ✅ **Reusability**: Core logic reused across different provisioning tools
- ✅ **Template for Future**: All new capabilities follow this pattern

---

## 🔧 Tool System Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                      TOOL MANAGER                                │
│              (Dynamic Registration System)                       │
│                                                                  │
│  Decorator Pattern:                                              │
│  ┌────────────────────────────────────────────────────────────┐ │
│  │  @tool_manager.register("Tool description")                │ │
│  │  def my_tool(param: str) -> str:                           │ │
│  │      return json.dumps(result)                             │ │
│  └────────────────────────────────────────────────────────────┘ │
│                           ⬇                                      │
│  Auto-generates OpenAI function schema:                          │
│  ┌────────────────────────────────────────────────────────────┐ │
│  │  {                                                          │ │
│  │    "name": "my_tool",                                       │ │
│  │    "description": "Tool description",                       │ │
│  │    "parameters": {                                          │ │
│  │      "type": "object",                                      │ │
│  │      "properties": {"param": {"type": "string"}},          │ │
│  │      "required": ["param"]                                  │ │
│  │    }                                                        │ │
│  │  }                                                          │ │
│  └────────────────────────────────────────────────────────────┘ │
│                                                                  │
│  Registered Tools:                                               │
│  ┌────────────────────────────────────────────────────────────┐ │
│  │  1️⃣ select_capabilities                                    │ │
│  │     → Validates capability names from registry             │ │
│  │     → Prevents hallucination                               │ │
│  │                                                             │ │
│  │  2️⃣ suggest_naming                                         │ │
│  │     → Generates Azure-compliant names                      │ │
│  │     → Provides alternatives                                │ │
│  │                                                             │ │
│  │  3️⃣ estimate_cost                                          │ │
│  │     → Calculates monthly costs                             │ │
│  │     → Provides breakdown by resource                       │ │
│  │                                                             │ │
│  │  4️⃣ execute_deployment                                     │ │
│  │     → Triggers capability.plan() → capability.execute()    │ │
│  │     → Returns deployment results                           │ │
│  └────────────────────────────────────────────────────────────┘ │
│                                                                  │
│  ✅ Scales to 100+ tools without code changes                   │
│  ✅ No hardcoded if/elif dispatch chains                        │
│  ✅ Type-safe with auto-validation                              │
└─────────────────────────────────────────────────────────────────┘
```

---

## 🛡️ Capability Registry (Anti-Hallucination)

```
┌─────────────────────────────────────────────────────────────────┐
│              CAPABILITY REGISTRY PATTERN                         │
│                                                                  │
│  Problem: LLMs hallucinate non-existent capabilities             │
│  Solution: Validate all capability names against registry        │
│                                                                  │
│  ┌────────────────────────────────────────────────────────────┐ │
│  │  Registration:                                              │ │
│  │                                                             │ │
│  │  capability_registry.register(                             │ │
│  │      name="provision_databricks",                          │ │
│  │      description="Provision Databricks workspace",         │ │
│  │      tags=["azure", "databricks", "analytics"]             │ │
│  │  )                                                          │ │
│  └────────────────────────────────────────────────────────────┘ │
│                           ⬇                                      │
│  ┌────────────────────────────────────────────────────────────┐ │
│  │  LLM Request:                                               │ │
│  │  "I need a data warehouse" → LLM thinks "provision_synapse"│ │
│  └────────────────────────────────────────────────────────────┘ │
│                           ⬇                                      │
│  ┌────────────────────────────────────────────────────────────┐ │
│  │  Validation:                                                │ │
│  │  capability_registry.validate("provision_synapse")         │ │
│  │  └─▶ ❌ REJECTED: "Unknown capability 'provision_synapse'" │ │
│  │                                                             │ │
│  │  LLM sees error → Rephrases → Uses valid capability        │ │
│  └────────────────────────────────────────────────────────────┘ │
│                                                                  │
│  ✅ Prevents deployment of non-existent infrastructure          │
│  ✅ Clear error messages guide LLM to correct capabilities      │
│  ✅ Semantic understanding (LLM) + Validation (Registry)        │
└─────────────────────────────────────────────────────────────────┘
```

---

## 📊 Technology Stack

```
┌─────────────────────────────────────────────────────────────────┐
│                        TECHNOLOGY CHOICES                        │
│                                                                  │
│  Layer              Technology           Purpose                │
│  ──────────────────────────────────────────────────────────────  │
│  🤖 Agent          MAF 1.0.0b251105      Conversation mgmt      │
│  🧠 LLM            Azure OpenAI GPT-4o   Function calling       │
│  📋 Validation     Pydantic 2.5+         Type-safe models       │
│  📝 Templates      Jinja2                Terraform generation   │
│  🏗️ IaC            Terraform 1.5+        Infrastructure         │
│  ☁️ Cloud          Azure (azurerm)       Resource deployment    │
│  🎯 Platform       Databricks            Data/ML workloads      │
│  🧪 Testing        pytest + asyncio      Test suite (94 tests)  │
│                                                                  │
│  Why These Choices?                                              │
│  ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━  │
│  • MAF: Automatic context, middleware, Azure integration        │
│  • GPT-4o: Function calling, structured outputs, 128K context   │
│  • Pydantic: Type safety, auto-validation, schema generation    │
│  • Terraform: Industry standard, provider ecosystem, state mgmt │
└─────────────────────────────────────────────────────────────────┘
```

---

## ✅ Current Status

```
┌─────────────────────────────────────────────────────────────────┐
│                       IMPLEMENTATION STATUS                      │
│                                                                  │
│  ✅ COMPLETED PHASES:                                            │
│                                                                  │
│  Phase 0:  MAF Integration                    [6 tests]         │
│  Phase 1:  Conversational Orchestrator        [9 tests]         │
│  Phase 1.5: Tool Registry Pattern             [included]        │
│  Phase 1.6: Capability Registry               [included]        │
│  Phase 2:  Capability Integration             [8 tests]         │
│  Nov 10:   Architecture Refactoring           [cleanup]         │
│                                                                  │
│  📊 Test Coverage: 94/94 tests passing (100%)                   │
│  ⏱️ Deployment Time: ~13 minutes end-to-end                     │
│  🎯 Production Ready: ✅ Verified in Azure                       │
│                                                                  │
│  ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━  │
│                                                                  │
│  🚀 FUTURE PHASES (Post-Spike):                                 │
│                                                                  │
│  Phase 3:  State Persistence & Robustness                       │
│            • Resume interrupted deployments                     │
│            • Comprehensive error handling                       │
│                                                                  │
│  Phase 4:  Second Capability (Azure OpenAI)                     │
│            • Multi-capability workflows                         │
│            • Cross-capability dependencies                      │
│                                                                  │
│  Phase 5:  Enterprise Features                                  │
│            • RBAC, cost budgets, approvals                      │
│            • Monitoring, alerting, integrations                 │
└─────────────────────────────────────────────────────────────────┘
```

---

## 🎓 Key Design Patterns

### 1. **Decorator-Based Registration**
```python
@tool_manager.register("Tool description")
def my_tool(param: str) -> str:
    return result
```
**Benefit**: Add tools without modifying core routing code

### 2. **Three-Layer Architecture**
- **Core**: Business logic (portable, IaC-agnostic)
- **Models**: Data structures (pure, validated)
- **Provisioning**: Infrastructure deployment (swappable)

**Benefit**: Clear separation, independent testing, future-proof

### 3. **Registry Pattern**
```python
capability_registry.register(name, description, tags)
capability_registry.validate(name) → bool
```
**Benefit**: Prevents LLM hallucination, enables dynamic discovery

### 4. **Public API Pattern**
```python
from capabilities.databricks import DatabricksCapability
```
**Benefit**: Clean imports, encapsulation, versioning

---

## 📞 Entry Points

**Main CLI**:
```bash
python cli_maf.py
```

**Key Classes**:
- `orchestrator.InfrastructureOrchestrator` - Conversation manager
- `capabilities.databricks.DatabricksCapability` - Databricks provisioning
- `capabilities.base.BaseCapability` - Capability interface

**Configuration**:
- `.env` file with Azure OpenAI credentials
- `capabilities/databricks/core/config.py` for Databricks config

---

**Last Updated**: November 10, 2025
**Status**: Production-Ready
**Test Coverage**: 94/94 (100%)
**Deployment Time**: ~13 minutes
