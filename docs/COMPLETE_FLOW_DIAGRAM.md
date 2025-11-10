# Complete Visual Flow: User Query → Deployed Infrastructure

**Last Updated**: November 10, 2025
**Status**: Current Implementation with November 10 Optimizations

---

## 🎯 Complete End-to-End Flow

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│  👤 USER INPUT                                                                   │
│  "I want provision a databricks workspace for data analytics"                   │
│                                                                                  │
│  CLI: cli_maf.py captures input → orchestrator.process_message()                │
└─────────────────────────────────┬───────────────────────────────────────────────┘
                                  │
                                  ▼
┌─────────────────────────────────────────────────────────────────────────────────┐
│  🤖 ORCHESTRATOR (MAF + Azure OpenAI GPT-4o)                                    │
│  File: orchestrator/orchestrator_agent.py                                       │
│                                                                                  │
│  ┌───────────────────────────────────────────────────────────────────────────┐ │
│  │  STEP 1: Understand Intent & Select Capability                            │ │
│  │  LLM analyzes: "databricks workspace for data analytics"                  │ │
│  │  ↓                                                                         │ │
│  │  Calls Tool: select_capabilities(["provision_databricks"])                │ │
│  │     File: orchestrator/tools.py                                           │ │
│  │     ↓                                                                      │ │
│  │     Validates against CapabilityRegistry → ✅ Valid                        │ │
│  │     File: orchestrator/capability_registry.py                             │ │
│  └───────────────────────────────────────────────────────────────────────────┘ │
│                                                                                  │
│  ┌───────────────────────────────────────────────────────────────────────────┐ │
│  │  STEP 2: Multi-Turn Parameter Gathering                                   │ │
│  │  Orchestrator: "What team will use this workspace?"                       │ │
│  │  Orchestrator: "What environment (dev/staging/prod)?"                     │ │
│  │  Orchestrator: "Which Azure region?"                                      │ │
│  │  ↓                                                                         │ │
│  │  User: "team=data-analytics-demo1, env=dev, region=eastus"               │ │
│  │  ↓                                                                         │ │
│  │  LLM extracts ALL parameters from single message:                         │ │
│  │    • team: "data-analytics-demo1"                                         │ │
│  │    • environment: "dev"                                                   │ │
│  │    • region: "eastus"                                                     │ │
│  └───────────────────────────────────────────────────────────────────────────┘ │
│                                                                                  │
│  ┌───────────────────────────────────────────────────────────────────────────┐ │
│  │  STEP 3: Generate Naming Suggestions                                      │ │
│  │  Calls Tool: suggest_naming(                                              │ │
│  │      team="data-analytics-demo1",                                         │ │
│  │      environment="dev",                                                   │ │
│  │      resource_type="databricks"                                           │ │
│  │  )                                                                         │ │
│  │  ↓                                                                         │ │
│  │  Returns: {                                                                │ │
│  │    primary: "data-analytics-demo1-dev",                                   │ │
│  │    alternatives: [                                                        │ │
│  │      "dbw-data-analytics-demo1-dev",                                      │ │
│  │      "data-analytics-demo1-databricks-dev"                                │ │
│  │    ]                                                                       │ │
│  │  }                                                                         │ │
│  └───────────────────────────────────────────────────────────────────────────┘ │
│                                                                                  │
│  ┌───────────────────────────────────────────────────────────────────────────┐ │
│  │  STEP 4: Estimate Costs                                                   │ │
│  │  Calls Tool: estimate_cost(                                               │ │
│  │      capability="provision_databricks",                                   │ │
│  │      parameters={                                                         │ │
│  │        team: "data-analytics-demo1",                                      │ │
│  │        environment: "dev",                                                │ │
│  │        region: "eastus",                                                  │ │
│  │        workload_type: "data_engineering"                                  │ │
│  │      }                                                                     │ │
│  │  )                                                                         │ │
│  │  ↓                                                                         │ │
│  │  Returns: {                                                                │ │
│  │    monthly_estimate: 834.0,                                               │ │
│  │    breakdown: [                                                           │ │
│  │      {item: "Databricks Workspace", cost: 0},                             │ │
│  │      {item: "Standard Cluster", cost: 784},                               │ │
│  │      {item: "Azure Storage", cost: 50}                                    │ │
│  │    ],                                                                      │ │
│  │    currency: "USD",                                                       │ │
│  │    confidence: "medium"                                                   │ │
│  │  }                                                                         │ │
│  └───────────────────────────────────────────────────────────────────────────┘ │
│                                                                                  │
│  ┌───────────────────────────────────────────────────────────────────────────┐ │
│  │  STEP 5: Present Plan & Get Approval                                      │ │
│  │  Orchestrator presents:                                                   │ │
│  │    • Workspace name: "data-analytics-demo1-dev"                           │ │
│  │    • Monthly cost: $834                                                   │ │
│  │    • Resource breakdown                                                   │ │
│  │  ↓                                                                         │ │
│  │  User: "go ahead" ← Approval trigger phrase                               │ │
│  └───────────────────────────────────────────────────────────────────────────┘ │
│                                                                                  │
│  ┌───────────────────────────────────────────────────────────────────────────┐ │
│  │  STEP 6: Execute Deployment                                               │ │
│  │  Calls Tool: execute_deployment(                                          │ │
│  │      capability_name="provision_databricks",                              │ │
│  │      parameters={                                                         │ │
│  │        team: "data-analytics-demo1",                                      │ │
│  │        environment: "dev",                                                │ │
│  │        region: "eastus"                                                   │ │
│  │      }                                                                     │ │
│  │  )                                                                         │ │
│  │  File: orchestrator/tools.py                                              │ │
│  └───────────────────────────────────────────────────────────────────────────┘ │
└─────────────────────────────────┬───────────────────────────────────────────────┘
                                  │
                                  ▼
┌─────────────────────────────────────────────────────────────────────────────────┐
│  ⚙️ execute_deployment Tool                                                      │
│  File: orchestrator/tools.py (lines 21-68)                                      │
│                                                                                  │
│  Calls: await orchestrator.execute_capability(                                  │
│      capability_name="provision_databricks",                                    │
│      user_request="Deploy infrastructure",                                      │
│      parameters={team, environment, region, ...}                                │
│  )                                                                               │
└─────────────────────────────────┬───────────────────────────────────────────────┘
                                  │
                                  ▼
┌─────────────────────────────────────────────────────────────────────────────────┐
│  🎯 orchestrator.execute_capability()                                           │
│  File: orchestrator/orchestrator_agent.py (lines 250-300)                      │
│                                                                                  │
│  Step 1: Build Context                                                          │
│  context = CapabilityContext(                                                   │
│      capability_name="provision_databricks",                                    │
│      user_request="Deploy infrastructure",                                      │
│      parameters={team, environment, region, ...}                                │
│  )                                                                               │
│                                                                                  │
│  Step 2: Execute Capability Lifecycle                                           │
│  ├─ plan = await capability.plan(context)         ← Generate deployment plan    │
│  └─ result = await capability.execute(plan)       ← Deploy infrastructure       │
└─────────────────────────────────┬───────────────────────────────────────────────┘
                                  │
                                  ▼
┌─────────────────────────────────────────────────────────────────────────────────┐
│  🔧 DATABRICKS CAPABILITY - plan() Method                                       │
│  File: capabilities/databricks/capability.py (lines 71-150)                     │
│                                                                                  │
│  ┏━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┓  │
│  ┃  STEP 1: Build InfrastructureRequest                                    ┃  │
│  ┃  Method: _build_infrastructure_request(context)                         ┃  │
│  ┃  File: capabilities/databricks/capability.py (lines 255-290)            ┃  │
│  ┃                                                                          ┃  │
│  ┃  ✨ OPTIMIZATION (November 10, 2025):                                    ┃  │
│  ┃                                                                          ┃  │
│  ┃  required_params = self.get_required_parameters()                       ┃  │
│  ┃  # Returns: ["team", "environment", "region"]                           ┃  │
│  ┃                                                                          ┃  │
│  ┃  has_all_required = all(param in context.parameters for param in ...)   ┃  │
│  ┃                                                                          ┃  │
│  ┃  IF all required params present:                                        ┃  │
│  ┃     ✅ SKIP EXPENSIVE LLM CALL (Save cost + latency)                     ┃  │
│  ┃     ✅ Build directly from parameters                                    ┃  │
│  ┃                                                                          ┃  │
│  ┃     team = context.parameters["team"]                                   ┃  │
│  ┃     environment = context.parameters["environment"]                     ┃  │
│  ┃                                                                          ┃  │
│  ┃     # Auto-generate workspace name                                      ┃  │
│  ┃     workspace_name = context.parameters.get("workspace_name")           ┃  │
│  ┃     if not workspace_name:                                              ┃  │
│  ┃         workspace_name = f"{team}-{environment}"                        ┃  │
│  ┃         # "data-analytics-demo1-dev"                                    ┃  │
│  ┃                                                                          ┃  │
│  ┃     infra_request = InfrastructureRequest(                              ┃  │
│  ┃         team="data-analytics-demo1",                                    ┃  │
│  ┃         environment="dev",                                              ┃  │
│  ┃         region="eastus",                                                ┃  │
│  ┃         workspace_name="data-analytics-demo1-dev",  ← Auto-generated!   ┃  │
│  ┃         enable_gpu=False,                                               ┃  │
│  ┃         workload_type="data_engineering"                                ┃  │
│  ┃     )                                                                    ┃  │
│  ┃                                                                          ┃  │
│  ┃  ELSE (missing params):                                                 ┃  │
│  ┃     ❌ Fallback to IntentParser (Azure OpenAI GPT-4o call)              ┃  │
│  ┃     File: capabilities/databricks/core/intent_parser.py                 ┃  │
│  ┃                                                                          ┃  │
│  ┃     request_text = self._build_request_text(context)                    ┃  │
│  ┃     infra_request = self.intent_parser.recognize_intent(request_text)   ┃  │
│  ┃                                                                          ┃  │
│  ┃     # Uses Azure OpenAI function calling to extract:                    ┃  │
│  ┃     # team, environment, region, workload_type, enable_gpu              ┃  │
│  ┃     # Auto-generates workspace_name if not provided                     ┃  │
│  ┗━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┛  │
│                                                                                  │
│  ┏━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┓  │
│  ┃  STEP 2: Make Configuration Decisions                                   ┃  │
│  ┃  Component: DecisionMaker                                               ┃  │
│  ┃  File: capabilities/databricks/core/decision_maker.py                   ┃  │
│  ┃                                                                          ┃  │
│  ┃  decision = self.decision_maker.make_decision(infra_request)            ┃  │
│  ┃                                                                          ┃  │
│  ┃  Logic:                                                                  ┃  │
│  ┃  ├─ Determine workload size: small/medium/large                         ┃  │
│  ┃  │    Based on: workload_type, environment                              ┃  │
│  ┃  │                                                                       ┃  │
│  ┃  ├─ Select instance types:                                              ┃  │
│  ┃  │    enable_gpu=False → Standard_DS3_v2 (4 vCPU, 14GB RAM)            ┃  │
│  ┃  │    enable_gpu=True  → Standard_NC6s_v3 (6 vCPU, 112GB RAM, V100)    ┃  │
│  ┃  │                                                                       ┃  │
│  ┃  ├─ Choose Databricks SKU:                                              ┃  │
│  ┃  │    dev → standard, staging → standard, prod → premium                ┃  │
│  ┃  │                                                                       ┃  │
│  ┃  ├─ Configure cluster autoscaling:                                      ┃  │
│  ┃  │    dev: min_workers=1, max_workers=3                                 ┃  │
│  ┃  │    staging: min_workers=2, max_workers=5                             ┃  │
│  ┃  │    prod: min_workers=3, max_workers=10                               ┃  │
│  ┃  │                                                                       ┃  │
│  ┃  ├─ Select Spark version:                                               ┃  │
│  ┃  │    GPU: 13.3.x-gpu-ml-scala2.12                                      ┃  │
│  ┃  │    CPU: 13.3.x-scala2.12                                             ┃  │
│  ┃  │                                                                       ┃  │
│  ┃  └─ Estimate monthly costs:                                             ┃  │
│  ┃       Workspace base fee: $0 (no charge for standard)                   ┃  │
│  ┃       Compute: instance_cost × avg_workers × hours_per_month            ┃  │
│  ┃       Storage: $50 for ~500GB                                           ┃  │
│  ┃                                                                          ┃  │
│  ┃  Result: InfrastructureDecision(                                        ┃  │
│  ┃      workspace_name="data-analytics-demo1-dev",                         ┃  │
│  ┃      resource_group_name="rg-data-analytics-demo1-dev",                 ┃  │
│  ┃      region="eastus",                                                   ┃  │
│  ┃      databricks_sku="standard",                                         ┃  │
│  ┃      driver_instance_type="Standard_DS3_v2",                            ┃  │
│  ┃      worker_instance_type="Standard_DS3_v2",                            ┃  │
│  ┃      min_workers=1,                                                     ┃  │
│  ┃      max_workers=3,                                                     ┃  │
│  ┃      spark_version="13.3.x-scala2.12",                                  ┃  │
│  ┃      autotermination_minutes=120,                                       ┃  │
│  ┃      estimated_monthly_cost=834.0                                       ┃  │
│  ┃  )                                                                       ┃  │
│  ┗━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┛  │
│                                                                                  │
│  ┏━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┓  │
│  ┃  STEP 3: Generate Terraform HCL                                         ┃  │
│  ┃  Component: TerraformGenerator                                          ┃  │
│  ┃  File: capabilities/databricks/provisioning/terraform/generator.py      ┃  │
│  ┃                                                                          ┃  │
│  ┃  terraform_files = self.terraform_generator.generate(decision)          ┃  │
│  ┃                                                                          ┃  │
│  ┃  Process:                                                                ┃  │
│  ┃  ├─ Load Jinja2 templates from:                                         ┃  │
│  ┃  │    capabilities/databricks/templates/                                ┃  │
│  ┃  │    ├─ main.tf.j2 (resource definitions)                              ┃  │
│  ┃  │    ├─ variables.tf.j2 (input variables)                              ┃  │
│  ┃  │    ├─ outputs.tf.j2 (output values)                                  ┃  │
│  ┃  │    ├─ provider.tf.j2 (azurerm, databricks providers)                 ┃  │
│  ┃  │    └─ terraform.tfvars.j2 (variable values)                          ┃  │
│  ┃  │                                                                       ┃  │
│  ┃  └─ Render each template with decision context                          ┃  │
│  ┃                                                                          ┃  │
│  ┃  Result: TerraformFiles(                                                ┃  │
│  ┃      main_tf="""                                                         ┃  │
│  ┃        resource "azurerm_resource_group" "main" {                       ┃  │
│  ┃          name     = "rg-data-analytics-demo1-dev"                       ┃  │
│  ┃          location = "eastus"                                            ┃  │
│  ┃        }                                                                 ┃  │
│  ┃        resource "azurerm_databricks_workspace" "main" {                 ┃  │
│  ┃          name                = "data-analytics-demo1-dev"               ┃  │
│  ┃          resource_group_name = azurerm_resource_group.main.name         ┃  │
│  ┃          location            = azurerm_resource_group.main.location     ┃  │
│  ┃          sku                 = "standard"                               ┃  │
│  ┃        }                                                                 ┃  │
│  ┃      """,                                                                ┃  │
│  ┃      variables_tf="""...""",                                            ┃  │
│  ┃      outputs_tf="""...""",                                              ┃  │
│  ┃      ...                                                                 ┃  │
│  ┃  )                                                                       ┃  │
│  ┗━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┛  │
│                                                                                  │
│  ┏━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┓  │
│  ┃  STEP 4: Terraform Plan (Dry-Run Preview)                               ┃  │
│  ┃  Component: TerraformExecutor                                           ┃  │
│  ┃  File: capabilities/databricks/provisioning/terraform/executor.py       ┃  │
│  ┃                                                                          ┃  │
│  ┃  working_dir = "terraform_workspaces/data-analytics-demo1-dev_plan"     ┃  │
│  ┃                                                                          ┃  │
│  ┃  plan_result = self.terraform_executor.execute_deployment(              ┃  │
│  ┃      terraform_files=terraform_files,                                   ┃  │
│  ┃      working_dir=working_dir,                                           ┃  │
│  ┃      auto_approve=False,                                                ┃  │
│  ┃      dry_run=True  ← Plan only, don't apply                             ┃  │
│  ┃  )                                                                       ┃  │
│  ┃                                                                          ┃  │
│  ┃  Execution:                                                              ┃  │
│  ┃  ├─ Write all 5 files to working_dir                                    ┃  │
│  ┃  ├─ Run: terraform init                                                 ┃  │
│  ┃  │    Downloads providers: azurerm, databricks                          ┃  │
│  ┃  ├─ Run: terraform plan -out=tfplan                                     ┃  │
│  ┃  │    Preview: 3 resources to create                                    ┃  │
│  ┃  │      + azurerm_resource_group.main                                   ┃  │
│  ┃  │      + azurerm_databricks_workspace.main                             ┃  │
│  ┃  │      + databricks_cluster.main                                       ┃  │
│  ┃  └─ Parse plan output and return preview                                ┃  │
│  ┗━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┛  │
│                                                                                  │
│  ┏━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┓  │
│  ┃  STEP 5: Return CapabilityPlan                                          ┃  │
│  ┃                                                                          ┃  │
│  ┃  Return: CapabilityPlan(                                                ┃  │
│  ┃      capability_name="provision_databricks",                            ┃  │
│  ┃      description="Provision Databricks workspace for ...",              ┃  │
│  ┃      resources=[                                                        ┃  │
│  ┃        {type: "Resource Group", name: "rg-data-analytics-demo1-dev"},   ┃  │
│  ┃        {type: "Databricks Workspace", name: "data-analytics-demo1-dev"},┃  │
│  ┃        {type: "Databricks Cluster", name: "...-cluster"}                ┃  │
│  ┃      ],                                                                  ┃  │
│  ┃      estimated_cost=834.0,                                              ┃  │
│  ┃      estimated_duration=15,  # minutes                                  ┃  │
│  ┃      requires_approval=True,                                            ┃  │
│  ┃      details={                                                           ┃  │
│  ┃        decision: InfrastructureDecision(...),                           ┃  │
│  ┃        terraform_files: TerraformFiles(...),                            ┃  │
│  ┃        terraform_plan: "Plan output...",                                ┃  │
│  ┃        working_dir: "terraform_workspaces/..."                          ┃  │
│  ┃      }                                                                   ┃  │
│  ┃  )                                                                       ┃  │
│  ┗━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┛  │
└─────────────────────────────────┬───────────────────────────────────────────────┘
                                  │
                                  │ Plan approved by user
                                  │
                                  ▼
┌─────────────────────────────────────────────────────────────────────────────────┐
│  🚀 DATABRICKS CAPABILITY - execute() Method                                    │
│  File: capabilities/databricks/capability.py (lines 152-235)                    │
│                                                                                  │
│  ┏━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┓  │
│  ┃  STEP 1: Reconstruct Context from Plan                                  ┃  │
│  ┃                                                                          ┃  │
│  ┃  working_dir = Path(plan.details["working_dir"])                        ┃  │
│  ┃  terraform_files_data = plan.details["terraform_files"]                 ┃  │
│  ┃                                                                          ┃  │
│  ┃  terraform_files = TerraformFiles(                                      ┃  │
│  ┃      main_tf=terraform_files_data["main.tf"],                           ┃  │
│  ┃      variables_tf=terraform_files_data["variables.tf"],                 ┃  │
│  ┃      outputs_tf=terraform_files_data["outputs.tf"],                     ┃  │
│  ┃      ...                                                                 ┃  │
│  ┃  )                                                                       ┃  │
│  ┗━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┛  │
│                                                                                  │
│  ┏━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┓  │
│  ┃  STEP 2: Terraform Apply (ACTUAL DEPLOYMENT!)                           ┃  │
│  ┃  Component: TerraformExecutor                                           ┃  │
│  ┃  File: capabilities/databricks/provisioning/terraform/executor.py       ┃  │
│  ┃                                                                          ┃  │
│  ┃  result = self.terraform_executor.execute_deployment(                   ┃  │
│  ┃      terraform_files=terraform_files,                                   ┃  │
│  ┃      working_dir=working_dir,                                           ┃  │
│  ┃      auto_approve=True,  ← User already approved in plan phase          ┃  │
│  ┃      dry_run=False  ← Actually deploy to Azure!                         ┃  │
│  ┃  )                                                                       ┃  │
│  ┃                                                                          ┃  │
│  ┃  Execution Timeline (~13 minutes):                                      ┃  │
│  ┃  00:00 - Run: terraform apply -auto-approve tfplan                      ┃  │
│  ┃  00:30 - Creating Resource Group                                        ┃  │
│  ┃  02:00 - Creating Databricks Workspace                                  ┃  │
│  ┃  08:00 - Configuring managed resource group                             ┃  │
│  ┃  10:00 - Creating Databricks Cluster                                    ┃  │
│  ┃  12:30 - Cluster starting...                                            ┃  │
│  ┃  13:00 - ✅ Deployment complete!                                         ┃  │
│  ┃                                                                          ┃  │
│  ┃  Post-Deployment:                                                        ┃  │
│  ┃  └─ Run: terraform output -json                                         ┃  │
│  ┃       Parse outputs:                                                    ┃  │
│  ┃       • workspace_url: "https://adb-123456.azuredatabricks.net"         ┃  │
│  ┃       • workspace_id: "123456789"                                       ┃  │
│  ┃       • resource_group: "rg-data-analytics-demo1-dev"                   ┃  │
│  ┗━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┛  │
│                                                                                  │
│  ┏━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┓  │
│  ┃  STEP 3: Return CapabilityResult                                        ┃  │
│  ┃                                                                          ┃  │
│  ┃  Return: CapabilityResult(                                              ┃  │
│  ┃      capability_name="provision_databricks",                            ┃  │
│  ┃      success=True,                                                      ┃  │
│  ┃      message="Successfully deployed Databricks workspace",              ┃  │
│  ┃      resources_created=[                                                ┃  │
│  ┃        {type: "Resource Group", ...},                                   ┃  │
│  ┃        {type: "Databricks Workspace", ...},                             ┃  │
│  ┃        {type: "Databricks Cluster", ...}                                ┃  │
│  ┃      ],                                                                  ┃  │
│  ┃      outputs={                                                           ┃  │
│  ┃        "workspace_url": "https://adb-123456.azuredatabricks.net",       ┃  │
│  ┃        "workspace_id": "123456789",                                     ┃  │
│  ┃        "resource_group": "rg-data-analytics-demo1-dev"                  ┃  │
│  ┃      },                                                                  ┃  │
│  ┃      duration_seconds=780  # ~13 minutes                                ┃  │
│  ┃  )                                                                       ┃  │
│  ┗━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┛  │
└─────────────────────────────────┬───────────────────────────────────────────────┘
                                  │
                                  ▼
┌─────────────────────────────────────────────────────────────────────────────────┐
│  ☁️ AZURE RESOURCES - Deployed & Running                                        │
│                                                                                  │
│  ✅ Resource Group: rg-data-analytics-demo1-dev                                 │
│     • Location: East US                                                         │
│     • Tags: {team: "data-analytics-demo1", env: "dev"}                          │
│                                                                                  │
│  ✅ Databricks Workspace: data-analytics-demo1-dev                              │
│     • SKU: Standard                                                             │
│     • URL: https://adb-123456789.azuredatabricks.net                            │
│     • Managed Resource Group: databricks-rg-...                                 │
│     • Public Network Access: Enabled                                            │
│                                                                                  │
│  ✅ Databricks Cluster: data-analytics-demo1-dev-cluster                        │
│     • Driver Node: Standard_DS3_v2                                              │
│     •   - 4 vCPU, 14 GB RAM                                                     │
│     • Worker Nodes: 1-3 autoscaling (Standard_DS3_v2)                           │
│     •   - Each: 4 vCPU, 14 GB RAM                                               │
│     • Spark Version: 13.3.x-scala2.12                                           │
│     • Autotermination: 120 minutes idle                                         │
│     • Status: RUNNING 🟢                                                        │
│                                                                                  │
│  ✅ Azure Storage Account: dbstorage (managed by Databricks)                    │
│     • Blob Storage: ~500GB capacity                                             │
│     • Replication: LRS (Locally Redundant Storage)                              │
│                                                                                  │
│  ┌─────────────────────────────────────────────────────────────────────────┐   │
│  │  📊 COST BREAKDOWN                                                       │   │
│  │  ─────────────────────────────────────────────────────────────────────  │   │
│  │  Databricks Workspace Base Fee:          $0.00/month                    │   │
│  │  Compute Cluster (Standard_DS3_v2):   $784.00/month                     │   │
│  │    • ~40 hours/week usage                                                │   │
│  │    • 1-3 workers autoscaling                                             │   │
│  │  Azure Blob Storage (~500GB):           $50.00/month                     │   │
│  │  ─────────────────────────────────────────────────────────────────────  │   │
│  │  TOTAL ESTIMATED MONTHLY COST:        $834.00/month                     │   │
│  └─────────────────────────────────────────────────────────────────────────┘   │
│                                                                                  │
│  ⏱️ Total Deployment Time: ~13 minutes                                          │
│  🎯 Status: Ready for Data Analytics Workloads! 🚀                              │
│                                                                                  │
│  Next Steps for User:                                                           │
│  1. Visit: https://adb-123456789.azuredatabricks.net                            │
│  2. Sign in with Azure credentials                                              │
│  3. Create notebooks and start analyzing data                                   │
│  4. Cluster will auto-terminate after 120 min of inactivity                     │
└─────────────────────────────────────────────────────────────────────────────────┘
```

---

## 🎯 Key Optimizations (November 10, 2025)

### 1. **LLM Call Optimization** (Cost & Latency Savings)
**Location**: `capabilities/databricks/capability.py::_build_infrastructure_request()`

**Before**:
```python
# Always called IntentParser (Azure OpenAI GPT-4o)
infra_request = self.intent_parser.recognize_intent(request_text)
# Cost: ~$0.01 per call, Latency: ~1-2 seconds
```

**After**:
```python
required_params = self.get_required_parameters()  # ["team", "environment", "region"]
has_all_required = all(param in context.parameters for param in required_params)

if has_all_required:
    # ✅ Skip LLM call - build directly from parameters
    workspace_name = f"{team}-{environment}"  # Auto-generate
    infra_request = InfrastructureRequest(...)
else:
    # ❌ Fallback to LLM only when needed
    infra_request = self.intent_parser.recognize_intent(request_text)
```

**Benefits**:
- ✅ Saves ~$0.01 per deployment when all params present
- ✅ Reduces latency by 1-2 seconds
- ✅ More predictable behavior
- ✅ Matches IntentParser name generation logic

### 2. **Single Source of Truth** (DRY Principle)
**Location**: `capabilities/databricks/capability.py`

**Before**: Required params hardcoded in 3 places
```python
# In _build_infrastructure_request():
required_params = ["team", "environment", "region"]

# In _build_request_text():
if "team" in context.parameters: ...
if "environment" in context.parameters: ...
if "region" in context.parameters: ...

# In get_required_parameters():
return ["team", "environment", "region"]
```

**After**: Single source of truth
```python
# Define once:
def get_required_parameters(self) -> list[str]:
    return ["team", "environment", "region"]

# Use everywhere:
required_params = self.get_required_parameters()
for param in self.get_required_parameters():
    ...
```

**Benefits**:
- ✅ Change once, updates everywhere
- ✅ Eliminates copy-paste errors
- ✅ Easier to maintain

### 3. **Bug Fix: Workspace Name Generation**
**Location**: `capabilities/databricks/capability.py::_build_infrastructure_request()`

**Problem**: When bypassing IntentParser, workspace_name was empty string `""`, causing Terraform error:
```
Error: "name" cannot be an empty string: ""
```

**Solution**: Auto-generate workspace_name matching IntentParser behavior:
```python
workspace_name = context.parameters.get("workspace_name")
if not workspace_name:
    workspace_name = f"{team}-{environment}"
    # "data-analytics-demo1-dev"
```

**Benefits**:
- ✅ Terraform validation passes
- ✅ Consistent naming convention
- ✅ Works with or without IntentParser

---

## 📊 Performance Metrics

| Metric | Value | Notes |
|--------|-------|-------|
| **Total Deployment Time** | ~13 minutes | terraform init + plan + apply |
| **LLM Calls (Optimized Path)** | 5-6 calls | Orchestrator conversation + tools |
| **LLM Calls (Non-Optimized)** | 6-7 calls | +1 for IntentParser |
| **Cost per Deployment** | ~$0.05-0.10 | Azure OpenAI GPT-4o token usage |
| **Infrastructure Cost** | $834/month | Workspace + compute + storage |
| **Test Coverage** | 94/94 tests passing | 100% success rate |

---

## 🔑 Key Files Reference

| Component | File Path | Lines | Purpose |
|-----------|-----------|-------|---------|
| **CLI Entry** | `cli_maf.py` | 69 | User interaction loop |
| **Orchestrator** | `orchestrator/orchestrator_agent.py` | 359 | MAF agent, conversation mgmt |
| **Tool Manager** | `orchestrator/tool_manager.py` | 253 | Dynamic tool registration |
| **Tools** | `orchestrator/tools.py` | 280 | 4 tools (select, suggest, estimate, execute) |
| **Capability Registry** | `orchestrator/capability_registry.py` | - | Anti-hallucination validation |
| **Databricks Capability** | `capabilities/databricks/capability.py` | 366 | Main capability implementation |
| **Intent Parser** | `capabilities/databricks/core/intent_parser.py` | - | NL → InfrastructureRequest |
| **Decision Maker** | `capabilities/databricks/core/decision_maker.py` | 246 | Config decisions + cost estimation |
| **Terraform Generator** | `capabilities/databricks/provisioning/terraform/generator.py` | - | Jinja2 → HCL |
| **Terraform Executor** | `capabilities/databricks/provisioning/terraform/executor.py` | - | Terraform subprocess mgmt |
| **Data Models** | `capabilities/databricks/models/schemas.py` | 188 | Pydantic schemas |
| **Config** | `capabilities/databricks/core/config.py` | - | Instance types, pricing, regions |

---

**Last Updated**: November 10, 2025
**Status**: Production-Ready with Optimizations
**Test Coverage**: 94/94 tests (100%)
**Deployment Success Rate**: ✅ Verified in Azure
