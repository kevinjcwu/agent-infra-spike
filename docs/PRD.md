# Product Requirements Document (PRD)
## Databricks Infrastructure Automation Agent - Spike/POC

**Version**: 1.0
**Date**: January 2025
**Status**: Spike/Proof of Concept
**Author**: Infrastructure Automation Team

---

## Executive Summary

Build a proof-of-concept AI agent that automates Databricks workspace provisioning, reducing deployment time from 3-4 hours (manual) to 15-20 minutes (automated). This spike validates the technical feasibility of using LLMs + Terraform to solve Rio's infrastructure provisioning bottleneck (1 month for 400 workspaces).

---

## Problem Statement

### Current State
- **Manual provisioning**: 3-4 hours per Databricks workspace
- **High error rate**: 20-30% of deployments require rework
- **Inconsistent configurations**: Each workspace slightly different
- **Poor scalability**: 400 workspaces take 1 month to provision
- **No self-service**: Teams must wait for infrastructure team

### Target State (Post-Spike Validation)
- **Automated provisioning**: 15-20 minutes per workspace
- **Near-zero errors**: Validated Terraform ensures consistency
- **Perfect consistency**: Every workspace follows same template
- **Scalable**: 400 workspaces in days, not months
- **Self-service capable**: Foundation for future agent-driven provisioning

---

## Goals & Success Criteria

### Primary Goal
**Prove that an LLM-powered agent can successfully provision production-grade Databricks infrastructure from natural language requests.**

### Success Criteria

#### Must Have (MVP for Spike)
1. ✅ **Natural Language Understanding**: Agent correctly parses user requests like "Create prod workspace for ML team in East US"
2. ✅ **Intelligent Decision Making**: Agent makes reasonable infrastructure decisions (instance types, SKU, configuration)
3. ✅ **Valid Terraform Generation**: Generates syntactically correct and functional Terraform code
4. ✅ **Successful Deployment**: Actually provisions working Databricks workspace in Azure
5. ✅ **Time Savings Demonstrated**: Completes in <20 minutes (vs 3-4 hours manual)
6. ✅ **Functional Verification**: Deployed workspace can run clusters and notebooks

#### Nice to Have (Future Enhancements)
- ⚠️ Complex approval workflows (show both auto and approval modes)
- ⚠️ Cost optimization recommendations
- ⚠️ Multi-workspace orchestration
- ⚠️ Rollback capabilities
- ⚠️ Advanced error handling

#### Out of Scope (For Spike)
- ❌ Integration with Jira/Azure DevOps/ServiceNow
- ❌ Production monitoring and alerting
- ❌ Continuous compliance checking
- ❌ Multi-tenancy support
- ❌ Advanced security hardening
- ❌ Cost tracking and chargebacks
- ❌ Disaster recovery
- ❌ Cross-cloud support

---

## User Stories

### US-001: Natural Language Request (P0)
**As a** data platform engineer
**I want to** describe infrastructure needs in natural language
**So that** I don't need to write Terraform or click through Azure portal

**Acceptance Criteria:**
- Agent accepts text input: "Create a production workspace for the ML team in East US with GPU support"
- Agent extracts key parameters: team=ML, env=prod, region=eastus, gpu=true
- Agent confirms understanding before proceeding

**Example Input/Output:**
```
Input: "Create prod workspace for ML team in East US"

Output:
✓ Detected: workspace for ML team
✓ Environment: production
✓ Location: East US
✓ Special requirements: None specified (will use defaults)
```

---

### US-002: Intelligent Configuration Selection (P0)
**As a** infrastructure agent
**I want to** choose appropriate instance types and configurations
**So that** workspaces are right-sized for their workload

**Acceptance Criteria:**
- ML team request → suggests GPU instances
- Production environment → selects Premium SKU
- Dev environment → selects smaller instances
- Provides cost estimate before deployment

**Example:**
```
Input: "ML team, production"

Decision:
- Instance types: Standard_NC6s_v3 (GPU)
- SKU: Premium (required for VNet)
- Cluster policy: ML Production
- Estimated cost: $4,200/month
```

---

### US-003: Terraform Code Generation (P0)
**As a** infrastructure agent
**I want to** generate valid Terraform configuration
**So that** infrastructure can be provisioned reliably

**Acceptance Criteria:**
- Generates main.tf, variables.tf, terraform.tfvars
- Uses pre-built Terraform module (not raw resources)
- All required parameters are populated
- Code passes `terraform validate`
- Code is human-readable

**Example Generated File Structure:**
```
generated/
├── main.tf              # Module invocation
├── variables.tf         # Variable definitions
├── terraform.tfvars     # Actual values
└── backend.tf          # Remote state config
```

---

### US-004: Automated Deployment (P0)
**As a** infrastructure agent
**I want to** execute Terraform deployment automatically
**So that** infrastructure is provisioned without manual intervention

**Acceptance Criteria:**
- Runs `terraform init` successfully
- Runs `terraform plan` and displays preview
- Runs `terraform apply` (with optional approval gate)
- Handles Terraform output and errors
- Returns workspace URL and key details

**Execution Flow:**
```
1. terraform init      (30 seconds)
2. terraform plan      (45 seconds)
3. [Optional: Wait for approval]
4. terraform apply     (15-18 minutes)
5. Extract outputs     (5 seconds)
```

---

### US-005: Deployment Verification (P0)
**As a** platform engineer
**I want to** verify the workspace is functional
**So that** I can confirm the deployment succeeded

**Acceptance Criteria:**
- Returns workspace URL
- Returns firewall public IP
- Confirms workspace is in "Running" state
- Can create and start a test cluster
- Can run a simple notebook

**Example Output:**
```
✅ Deployment Complete!

Workspace URL: https://adb-1234567890.19.azuredatabricks.net
Firewall IP: 40.112.72.145
Status: Running
Time taken: 17 minutes 32 seconds

Verification:
✓ Workspace accessible
✓ Test cluster started successfully
✓ Notebook execution confirmed
```

---

### US-006: Approval Mode Demo (P1)
**As a** platform engineer
**I want to** review and approve infrastructure before deployment
**So that** I maintain control over production changes

**Acceptance Criteria:**
- Agent shows plan before applying
- Waits for explicit "yes" confirmation
- Can cancel deployment
- Supports both auto-approve and manual modes

**Example:**
```
Terraform will create 15 resources:
- 1 VNet
- 2 Subnets
- 2 NSGs
- 1 Firewall
- 1 Databricks Workspace
- ...

Estimated cost: $4,200/month

Approve deployment? (yes/no): _
```

---

## Technical Architecture

### High-Level Components

```
┌─────────────────────────────────────────────────────────┐
│  User Interface (CLI)                                   │
│  - Simple command-line input                            │
│  - Text-based interaction                               │
└────────────────────┬────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────┐
│  LLM Agent (OpenAI GPT-4)                               │
│  - Natural language parsing                             │
│  - Parameter extraction                                 │
│  - Intent recognition                                   │
└────────────────────┬────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────┐
│  Decision Engine (Python)                               │
│  - Workload type inference                              │
│  - Instance type selection                              │
│  - Cost estimation                                      │
│  - Configuration validation                             │
└────────────────────┬────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────┐
│  Terraform Generator (Jinja2 Templates)                 │
│  - Template-based HCL generation                        │
│  - Variable substitution                                │
│  - File system operations                               │
└────────────────────┬────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────┐
│  Terraform Executor (Subprocess)                        │
│  - terraform init                                       │
│  - terraform plan                                       │
│  - terraform apply                                      │
│  - Output parsing                                       │
└────────────────────┬────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────┐
│  Azure Infrastructure                                   │
│  - VNet, Subnets, NSGs                                  │
│  - Azure Firewall                                       │
│  - Databricks Workspace                                 │
│  - Storage Accounts                                     │
└─────────────────────────────────────────────────────────┘
```

### Technology Stack

| Component | Technology | Justification |
|-----------|------------|---------------|
| **Language** | Python 3.10+ | Rich ecosystem, LLM libraries, subprocess management |
| **LLM** | OpenAI GPT-4 | Best-in-class understanding, function calling support |
| **IaC** | Terraform 1.5+ | Industry standard, Azure provider maturity |
| **Templating** | Jinja2 | Python-native, HCL generation |
| **Cloud** | Microsoft Azure | Rio's target platform |
| **CLI Framework** | Click or Typer | User-friendly CLI creation |

---

## Data Models

### InfrastructureRequest
```python
@dataclass
class InfrastructureRequest:
    """User's infrastructure request parsed by LLM"""
    workspace_name: str          # e.g., "ml-team-prod-001"
    team: str                    # e.g., "ML Team", "Data Science"
    environment: str             # e.g., "dev", "staging", "prod"
    region: str                  # e.g., "eastus", "westus2"
    enable_gpu: bool             # Default: False
    workload_type: str           # e.g., "ml_training", "data_engineering"
    cost_limit: Optional[float]  # Max monthly cost in USD
    requester: str               # Email of requester
```

### InfrastructureDecision
```python
@dataclass
class InfrastructureDecision:
    """Agent's infrastructure decisions"""
    workspace_name: str
    template_name: str           # e.g., "gpu-workspace", "standard-workspace"
    sku: str                     # e.g., "premium"
    instance_types: List[str]    # e.g., ["Standard_NC6s_v3"]
    cluster_config: dict         # Min/max workers, auto-termination
    estimated_cost: float        # Monthly estimate in USD
    reasoning: str               # Why these decisions were made
    vnet_address: str            # e.g., "10.100.0.0/16"
```

### DeploymentResult
```python
@dataclass
class DeploymentResult:
    """Result of Terraform execution"""
    success: bool
    workspace_url: Optional[str]
    firewall_ip: Optional[str]
    resource_group: str
    duration_seconds: float
    resources_created: int
    error_message: Optional[str]
    terraform_outputs: dict
```

---

## API Specifications

### Core Agent Interface

```python
class InfrastructureAgent:
    """Main agent orchestrator"""

    def __init__(self, config: AgentConfig):
        """Initialize agent with configuration"""
        pass

    def process_request(
        self,
        user_message: str,
        auto_approve: bool = False
    ) -> DeploymentResult:
        """
        Process natural language request and deploy infrastructure

        Args:
            user_message: Natural language request
            auto_approve: Skip approval prompt if True

        Returns:
            DeploymentResult with workspace details

        Raises:
            ValidationError: If request cannot be parsed
            DeploymentError: If Terraform execution fails
        """
        pass
```

### LLM Integration

```python
class IntentRecognizer:
    """Parse natural language into structured requests"""

    def recognize(
        self,
        user_message: str
    ) -> InfrastructureRequest:
        """
        Parse natural language into structured parameters

        Example:
            Input: "Create prod workspace for ML team in East US"
            Output: InfrastructureRequest(
                team="ML Team",
                environment="prod",
                region="eastus",
                ...
            )
        """
        pass
```

### Decision Engine

```python
class DecisionEngine:
    """Make infrastructure configuration decisions"""

    def decide(
        self,
        request: InfrastructureRequest
    ) -> InfrastructureDecision:
        """
        Determine optimal infrastructure configuration

        Logic:
        - ML team + GPU → NC6s_v3 instances
        - Production → Premium SKU, larger instances
        - Dev → Standard SKU, smaller instances
        - Cost estimates based on Azure pricing
        """
        pass
```

### Terraform Generator

```python
class TerraformGenerator:
    """Generate Terraform configuration files"""

    def generate(
        self,
        decision: InfrastructureDecision
    ) -> Dict[str, str]:
        """
        Generate Terraform files from decisions

        Returns:
            Dictionary of filename -> content
            {
                "main.tf": "...",
                "variables.tf": "...",
                "terraform.tfvars": "..."
            }
        """
        pass
```

### Terraform Executor

```python
class TerraformExecutor:
    """Execute Terraform commands"""

    def execute_workflow(
        self,
        working_dir: str,
        auto_approve: bool = False
    ) -> DeploymentResult:
        """
        Run complete Terraform workflow

        Steps:
        1. terraform init
        2. terraform plan
        3. [Optional: Wait for approval]
        4. terraform apply
        5. Parse outputs

        Returns:
            DeploymentResult with workspace details
        """
        pass
```

---

## Implementation Plan

### Phase 1: Foundation (Week 1-2)
**Goal**: Understand the domain, build base Terraform module

**Tasks:**
1. Complete Databricks hands-on labs (US-001 prerequisite)
   - Lab 1: Basic workspace (2 hours)
   - Lab 2: VNet injection (4 hours)
   - Lab 3: Production setup (5 hours)
   - Lab 4: Break things (2 hours)

2. Build Terraform module (US-003 dependency)
   - Module structure: main.tf, variables.tf, outputs.tf
   - VNet + subnets + NSGs
   - Azure Firewall + routing
   - Databricks workspace
   - Basic Unity Catalog setup
   - Test manual deployment end-to-end

**Deliverables:**
- ✅ Working Terraform module in `modules/databricks-workspace/`
- ✅ Manual deployment documentation
- ✅ Pain points identified for automation

---

### Phase 2: Agent Intelligence (Week 3)
**Goal**: Build LLM integration and decision engine

**Tasks:**
1. LLM Integration (US-001, US-002)
   - OpenAI API setup
   - Prompt engineering for intent recognition
   - Function calling for structured output
   - Parameter extraction and validation

2. Decision Engine (US-002)
   - Workload type inference rules
   - Instance type selection logic
   - Cost estimation formulas
   - Configuration templates

3. Integration Tests
   - Test various request patterns
   - Validate decision quality
   - Edge case handling

**Deliverables:**
- ✅ `intent_recognizer.py` - LLM integration
- ✅ `decision_engine.py` - Configuration logic
- ✅ Test suite with 10+ example requests

---

### Phase 3: End-to-End Integration (Week 4)
**Goal**: Connect all components and demonstrate working POC

**Tasks:**
1. Terraform Generator (US-003)
   - Jinja2 templates for HCL generation
   - Variable substitution
   - File writing operations

2. Terraform Executor (US-004)
   - Subprocess management
   - Command execution (init, plan, apply)
   - Output parsing
   - Error handling

3. Main Orchestrator (US-005)
   - Agent class that ties everything together
   - CLI interface
   - Approval workflow
   - Result display

4. Demo Preparation (US-006)
   - Demo script
   - Example requests
   - Success metrics calculation

**Deliverables:**
- ✅ `infrastructure_agent.py` - Main orchestrator
- ✅ `cli.py` - Command-line interface
- ✅ Working end-to-end demo
- ✅ Demo video and documentation

---

## File Structure

```
databricks-agent-spike/
├── README.md                          # Project overview and setup
├── requirements.txt                   # Python dependencies
├── .env.example                       # Environment variables template
├── .gitignore                         # Git ignore rules
│
├── modules/
│   └── databricks-workspace/          # Reusable Terraform module
│       ├── main.tf
│       ├── variables.tf
│       ├── outputs.tf
│       ├── networking.tf
│       ├── firewall.tf
│       ├── databricks.tf
│       └── unity-catalog.tf
│
├── agent/
│   ├── __init__.py
│   ├── infrastructure_agent.py        # Main orchestrator (US-005)
│   ├── intent_recognizer.py           # LLM integration (US-001)
│   ├── decision_engine.py             # Configuration logic (US-002)
│   ├── terraform_generator.py         # HCL generation (US-003)
│   ├── terraform_executor.py          # Terraform execution (US-004)
│   ├── models.py                      # Data classes
│   └── config.py                      # Configuration management
│
├── templates/                         # NOTE: Now at capabilities/databricks/templates/
│   ├── main.tf.j2                     # Jinja2 template for main.tf
│   ├── variables.tf.j2                # Jinja2 template for variables.tf
│   └── terraform.tfvars.j2            # Jinja2 template for tfvars
│
├── tests/
│   ├── test_intent_recognizer.py
│   ├── test_decision_engine.py
│   ├── test_terraform_generator.py
│   └── test_integration.py
│
├── examples/
│   ├── example_requests.txt           # Sample user inputs
│   └── demo_script.md                 # Demo walkthrough
│
├── generated/                         # Terraform files (gitignored)
│   └── workspace-xyz/
│       ├── main.tf
│       ├── variables.tf
│       └── terraform.tfvars
│
├── docs/
│   ├── architecture.md                # System architecture
│   ├── deployment-guide.md            # Deployment instructions
│   └── troubleshooting.md             # Common issues
│
└── cli.py                             # Command-line entry point
```

---

## Configuration

### Environment Variables
```bash
# .env
OPENAI_API_KEY=sk-...                  # OpenAI API key
AZURE_SUBSCRIPTION_ID=...              # Azure subscription
AZURE_TENANT_ID=...                    # Azure tenant
AZURE_CLIENT_ID=...                    # Service principal
AZURE_CLIENT_SECRET=...                # Service principal secret

# Agent Configuration
AGENT_MODE=auto                        # auto | approval
TERRAFORM_STATE_RESOURCE_GROUP=...     # For remote state
TERRAFORM_STATE_STORAGE_ACCOUNT=...    # For remote state
```

### Agent Configuration
```python
# agent/config.py
@dataclass
class AgentConfig:
    openai_api_key: str
    openai_model: str = "gpt-4"
    azure_subscription_id: str
    terraform_module_path: str = "./modules/databricks-workspace"
    working_directory: str = "./generated"
    auto_approve: bool = False
    cost_limit_default: float = 10000.0

    # Azure defaults
    default_region: str = "eastus"
    default_vnet_cidr: str = "10.100.0.0/16"
```

---

## Testing Strategy

### Unit Tests
```python
# Test intent recognition
def test_parse_simple_request():
    input = "Create workspace for ML team"
    result = recognizer.recognize(input)
    assert result.team == "ML Team"
    assert result.environment == "dev"  # default

def test_parse_complex_request():
    input = "Create prod workspace for data science in West US with GPU"
    result = recognizer.recognize(input)
    assert result.environment == "prod"
    assert result.region == "westus"
    assert result.enable_gpu == True

# Test decision engine
def test_ml_team_gets_gpu():
    request = InfrastructureRequest(team="ML", ...)
    decision = engine.decide(request)
    assert "NC" in decision.instance_types[0]  # GPU instance

def test_prod_gets_premium_sku():
    request = InfrastructureRequest(environment="prod", ...)
    decision = engine.decide(request)
    assert decision.sku == "premium"
```

### Integration Tests
```python
def test_end_to_end_request():
    """Test complete flow without actual deployment"""
    input = "Create dev workspace for analytics team"

    # Parse
    request = agent.parse_request(input)

    # Decide
    decision = agent.make_decision(request)

    # Generate
    files = agent.generate_terraform(decision)

    # Validate
    assert "main.tf" in files
    assert "terraform.tfvars" in files

    # Terraform validate (no actual apply)
    result = agent.validate_terraform(files)
    assert result.valid == True
```

### Manual Testing
```bash
# Test different request types
python cli.py --request "Create workspace for ML team" --dry-run
python cli.py --request "Prod workspace for data engineering in East US" --dry-run
python cli.py --request "Dev workspace with GPU" --dry-run

# Test actual deployment (use test subscription)
python cli.py --request "Test workspace" --auto-approve
```

---

## Demo Script

### Setup (Before Demo)
```bash
# 1. Ensure environment is configured
source .env
az login
terraform --version

# 2. Clean up any previous runs
rm -rf generated/*

# 3. Prepare demo terminal with large font
```

### Demo Flow (20 minutes)

**Part 1: The Problem (3 minutes)**
```bash
# Show manual process
# Open Azure Portal
# Navigate through: VNet creation → Subnet → NSG → Workspace
# "This takes 3-4 hours and is error-prone"
```

**Part 2: The Solution (2 minutes)**
```bash
# Show architecture diagram
# Explain: Natural Language → LLM → Terraform → Azure
```

**Part 3: Live Demo (12 minutes)**
```bash
# Start agent
python cli.py

# Enter request
> Create a production workspace for the ML team in East US with GPU support

# Watch agent work:
# [Shows understanding]
# [Shows decisions]
# [Shows cost estimate]
# [Shows Terraform plan]
# [Waits for approval]

# Type: yes

# Watch deployment:
# [Progress updates]
# [Resources being created]
# [Final result]

# Result:
# ✅ Workspace URL: https://adb-xxx...
# ✅ Firewall IP: 40.112.72.145
# ✅ Time: 17 minutes
```

**Part 4: Verification (2 minutes)**
```bash
# Open workspace in browser
# Create a cluster
# Show it's functional
```

**Part 5: Impact (1 minute)**
```bash
# Show metrics:
# Manual: 3-4 hours
# Automated: 18 minutes
# Time saved: 91%
#
# For 400 workspaces:
# Manual: 1 month
# Automated: 3 days (sequential) or 12 hours (parallel)
```

---

## Dependencies

### Python Packages
```txt
# requirements.txt
openai==1.3.0                  # LLM integration
pydantic==2.5.0               # Data validation
python-dotenv==1.0.0          # Environment management
jinja2==3.1.2                 # Template engine
click==8.1.7                  # CLI framework
azure-identity==1.15.0        # Azure authentication
azure-mgmt-resource==23.0.0   # Azure SDK
requests==2.31.0              # HTTP client
pyyaml==6.0.1                # YAML parsing
pytest==7.4.3                # Testing
```

### External Tools
- Terraform >= 1.5.0
- Azure CLI >= 2.50.0
- Python >= 3.10

### Azure Permissions Required
```yaml
# Service Principal needs:
- Contributor role on subscription (or resource groups)
- User Access Administrator (for role assignments)
- Network Contributor (for VNet operations)
```

---

## Risks & Mitigations

| Risk | Impact | Probability | Mitigation |
|------|--------|-------------|------------|
| **LLM misunderstands request** | High | Medium | Confirmation step, show parsed intent |
| **Terraform deployment fails** | High | Medium | Pre-flight validation, detailed error messages |
| **Azure quota limits hit** | Medium | Low | Check quotas before deployment |
| **Cost overruns** | High | Low | Cost estimation, approval gates |
| **Network configuration errors** | High | Medium | Use tested Terraform module |
| **State file corruption** | Medium | Low | Remote state with locking |
| **Authentication failures** | Medium | Low | Validate credentials at startup |

---

## Success Metrics

### Quantitative Metrics
| Metric | Target | How to Measure |
|--------|--------|----------------|
| **Deployment Time** | <20 minutes | Track from request to workspace URL |
| **Success Rate** | >90% | Successful deployments / total attempts |
| **Configuration Accuracy** | 100% | Manual review of generated configs |
| **Cost Estimation Accuracy** | ±10% | Compare estimate to actual first-month cost |
| **LLM Understanding Accuracy** | >95% | Parsed parameters match intent |

### Qualitative Metrics
- ✅ Demo receives positive feedback from stakeholders
- ✅ Code is maintainable and well-documented
- ✅ Terraform module is reusable
- ✅ Error messages are helpful
- ✅ Can explain decisions made by agent

---

## Future Enhancements (Post-Spike)

### Short-term (Next 1-2 months)
- Integration with Jira/Azure DevOps for request intake
- Advanced approval workflows (multi-stage, role-based)
- Cost tracking and budget alerts
- Batch provisioning (multiple workspaces)
- Slack/Teams notifications

### Medium-term (3-6 months)
- Workspace modification (not just creation)
- Decommissioning workflows
- Drift detection and remediation
- Advanced monitoring integration
- Self-service portal UI

### Long-term (6-12 months)
- Multi-cloud support (AWS, GCP)
- AI-driven cost optimization
- Predictive capacity planning
- Automated troubleshooting
- Full GitOps integration

---

## Acceptance Criteria (Definition of Done)

The spike is complete when:

1. ✅ **Code Complete**
   - All components implemented per technical spec
   - Unit tests pass (>80% coverage)
   - Integration tests pass

2. ✅ **Deployment Proven**
   - Successfully deployed 3+ workspaces from natural language
   - Each workspace is functional (can run clusters/notebooks)
   - Deployment time consistently <20 minutes

3. ✅ **Demo Ready**
   - 20-minute demo script prepared
   - Demo environment configured
   - Demo video recorded
   - Slide deck created

4. ✅ **Documentation Complete**
   - README with setup instructions
   - Architecture documentation
   - API documentation
   - Troubleshooting guide

5. ✅ **Stakeholder Review**
   - Demo presented to stakeholders
   - Feedback collected
   - Next steps agreed upon

---

## Appendix

### A. Example Requests

```text
# Simple requests
"Create workspace for data science team"
"Create ML workspace"
"Set up analytics environment"

# Detailed requests
"Create production workspace for ML team in East US with GPU support"
"Set up dev workspace for data engineering in West US, keep costs under $2k"
"Production Databricks for analytics team with high availability"

# Edge cases
"Create workspace" (missing information - agent should ask)
"Make me a really big expensive workspace" (cost controls should trigger)
"Workspace for stealth project X" (unknown team - agent should flag)
```

### B. Cost Estimation Formula

```python
def estimate_monthly_cost(decision: InfrastructureDecision) -> float:
    """Calculate estimated monthly infrastructure cost"""

    # Firewall (fixed)
    firewall_cost = 1.25 * 730  # $/hour * hours/month = $912.50

    # Storage (Unity Catalog)
    storage_cost = 50  # ~50GB estimated

    # Networking (VNet, NSG, etc.)
    networking_cost = 10  # Minimal

    # Compute (variable based on usage)
    instance_cost_per_hour = AZURE_PRICING[decision.instance_types[0]]
    dbu_cost_per_hour = DBU_PRICING[decision.sku][decision.cluster_type]

    avg_workers = (decision.cluster_config['min_workers'] +
                   decision.cluster_config['max_workers']) / 2

    # Assume 8 hours/day, 20 days/month for dev; 24/7 for prod
    hours_per_month = 730 if decision.environment == 'prod' else 160

    compute_cost = (instance_cost_per_hour + dbu_cost_per_hour) * \
                   avg_workers * hours_per_month

    total = firewall_cost + storage_cost + networking_cost + compute_cost

    return round(total, 2)
```

### C. Terraform Module Interface

```hcl
# Expected module usage
module "databricks_workspace" {
  source = "./modules/databricks-workspace"

  # Required
  workspace_prefix = "ml-team-prod"
  environment      = "prod"
  location         = "eastus"

  # Optional with defaults
  vnet_address_space       = ["10.100.0.0/16"]
  enable_unity_catalog     = true
  enable_private_endpoints = true
  instance_pool_type       = "Standard_NC6s_v3"

  # Tags
  tags = {
    Team       = "ML Team"
    CostCenter = "Engineering"
    ManagedBy  = "InfrastructureAgent"
  }
}
```

### D. Reference Architecture Diagram

```
┌──────────────────────────────────────────────────────────────┐
│                         User                                  │
└───────────────────────┬──────────────────────────────────────┘
                        │
                        │ "Create prod workspace for ML team"
                        │
┌───────────────────────▼──────────────────────────────────────┐
│                    CLI Interface                              │
│                  (cli.py)                                     │
└───────────────────────┬──────────────────────────────────────┘
                        │
┌───────────────────────▼──────────────────────────────────────┐
│              InfrastructureAgent                              │
│         (infrastructure_agent.py)                             │
│  ┌──────────────────────────────────────────────────────┐   │
│  │ 1. Parse → IntentRecognizer (LLM)                    │   │
│  │ 2. Decide → DecisionEngine (Rules + Logic)           │   │
│  │ 3. Generate → TerraformGenerator (Templates)         │   │
│  │ 4. Execute → TerraformExecutor (Subprocess)          │   │
│  │ 5. Verify → Result validation                        │   │
│  └──────────────────────────────────────────────────────┘   │
└───────────────────────┬──────────────────────────────────────┘
                        │
        ┌───────────────┼───────────────┐
        │               │               │
┌───────▼──────┐ ┌──────▼──────┐ ┌─────▼──────┐
│   OpenAI     │ │  Terraform  │ │   Azure    │
│   GPT-4      │ │    CLI      │ │    API     │
└──────────────┘ └──────┬──────┘ └────────────┘
                        │
                        │ Creates infrastructure
                        │
┌───────────────────────▼──────────────────────────────────────┐
│                  Azure Resources                              │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐       │
│  │   VNet   │ │   NSG    │ │Firewall  │ │Databricks│       │
│  └──────────┘ └──────────┘ └──────────┘ └──────────┘       │
└───────────────────────────────────────────────────────────────┘
```

---

## Glossary

| Term | Definition |
|------|------------|
| **Agent** | AI-powered software that can understand requests and take actions |
| **DBU** | Databricks Unit - pricing unit for Databricks processing |
| **HCL** | HashiCorp Configuration Language - Terraform's syntax |
| **IaC** | Infrastructure as Code - managing infrastructure through code |
| **LLM** | Large Language Model - AI model like GPT-4 |
| **NAT IP** | Network Address Translation IP - single public IP for egress |
| **NSG** | Network Security Group - Azure firewall rules for subnets |
| **SKU** | Stock Keeping Unit - Azure pricing tier (Standard/Premium) |
| **Spike** | Time-boxed investigation to prove technical feasibility |
| **UDR** | User Defined Route - custom routing rules in Azure |
| **VNet Injection** | Deploying Databricks clusters in customer-managed VNet |

---

## Sign-off

| Role | Name | Signature | Date |
|------|------|-----------|------|
| Product Owner | [Name] | _________ | _____ |
| Tech Lead | [Name] | _________ | _____ |
| Architect | [Name] | _________ | _____ |

---

**Document Version History**

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.0 | 2025-01-XX | Team | Initial PRD for spike |

---

**End of PRD**
