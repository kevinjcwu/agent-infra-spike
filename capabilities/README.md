# Infrastructure Capabilities

This directory contains all infrastructure provisioning capabilities. Each capability is a pluggable module that provisions specific Azure infrastructure.

## Structure

```
capabilities/
├── base.py                      # BaseCapability interface and data models
├── databricks/                  # Databricks workspace provisioning
│   ├── __init__.py
│   └── capability.py           # DatabricksCapability implementation
└── [future: openai/, firewall/, networking/, etc.]
```

## Capability Interface

All capabilities implement the `BaseCapability` abstract class:

```python
class BaseCapability(ABC):
    @property
    def name(self) -> str:
        """Unique capability identifier (e.g., 'provision_databricks')"""

    @property
    def description(self) -> str:
        """Human-readable description"""

    async def plan(self, context: CapabilityContext) -> CapabilityPlan:
        """Generate deployment plan without executing (dry-run)"""

    async def execute(self, plan: CapabilityPlan) -> CapabilityResult:
        """Execute approved deployment plan"""

    async def validate(self, context: CapabilityContext) -> tuple[bool, list[str]]:
        """Validate context before planning (optional)"""

    async def rollback(self, result: CapabilityResult) -> bool:
        """Rollback failed deployment (optional, future)"""
```

## Lifecycle

1. **Plan Phase**: `plan(context)` → generates CapabilityPlan
   - Analyzes user requirements
   - Makes configuration decisions
   - Generates infrastructure code (Terraform, ARM, etc.)
   - Estimates costs and resources
   - Returns plan for user review

2. **Validation Phase**: User reviews plan, orchestrator gets approval

3. **Execute Phase**: `execute(plan)` → returns CapabilityResult
   - Runs actual infrastructure deployment
   - Tracks progress
   - Captures outputs (URLs, IDs, credentials)
   - Returns success/failure status

## Data Models

### CapabilityContext
Input to `plan()` method:
```python
@dataclass
class CapabilityContext:
    user_request: str                    # Original natural language request
    capability_name: str                 # Name of this capability
    parameters: dict[str, any]           # Validated parameters from conversation
    metadata: dict[str, any] = field(default_factory=dict)  # Additional context
```

### CapabilityPlan
Output from `plan()` method:
```python
@dataclass
class CapabilityPlan:
    capability_name: str                 # Name of capability
    description: str                     # Human-readable summary
    resources: list[dict]                # Resources to be created
    estimated_cost: float                # Monthly cost estimate
    estimated_duration: int              # Deployment time (minutes)
    requires_approval: bool              # Whether user approval needed
    details: dict[str, any]              # Capability-specific details

    def to_summary(self) -> str:
        """Generate human-readable plan summary"""
```

### CapabilityResult
Output from `execute()` method:
```python
@dataclass
class CapabilityResult:
    capability_name: str                 # Name of capability
    success: bool                        # Deployment succeeded?
    message: str                         # Status message
    resources_created: list[dict] = field(default_factory=list)
    outputs: dict[str, any] = field(default_factory=dict)  # URLs, IDs, etc.
    error: str | None = None             # Error message if failed
    duration_seconds: float = 0.0        # Actual execution time

    def to_summary(self) -> str:
        """Generate human-readable result summary"""
```

## Adding a New Capability

### 1. Create Directory Structure

```bash
mkdir -p capabilities/<capability-name>
```

### 2. Create `__init__.py`

```python
from capabilities.<capability-name>.capability import <CapabilityClass>

__all__ = ["<CapabilityClass>"]
```

### 3. Create `capability.py`

```python
from capabilities.base import BaseCapability, CapabilityContext, CapabilityPlan, CapabilityResult

class <CapabilityClass>(BaseCapability):
    @property
    def name(self) -> str:
        return "provision_<resource>"

    @property
    def description(self) -> str:
        return "Provision <resource> infrastructure in Azure"

    async def plan(self, context: CapabilityContext) -> CapabilityPlan:
        # Implementation
        pass

    async def execute(self, plan: CapabilityPlan) -> CapabilityResult:
        # Implementation
        pass
```

### 4. Register in Orchestrator

In `orchestrator/orchestrator_agent.py`, add to `_register_capabilities()`:

```python
from capabilities.<capability-name> import <CapabilityClass>

def _register_capabilities(self):
    self.capabilities["provision_<resource>"] = <CapabilityClass>()
```

### 5. Register in Capability Registry

In `orchestrator/capability_registry.py`:

```python
capability_registry.register(
    name="provision_<resource>",
    description="Provision <resource> infrastructure",
    tags=["azure", "<category>"],
    required_params=["param1", "param2"],
    optional_params=["param3"]
)
```

### 6. Create Tests

Create `tests/test_<capability>_integration.py`:

```python
import pytest
from capabilities import CapabilityContext
from capabilities.<capability-name> import <CapabilityClass>

@pytest.mark.asyncio
async def test_capability_plan_generation():
    capability = <CapabilityClass>()
    context = CapabilityContext(
        user_request="Test request",
        capability_name="provision_<resource>",
        parameters={"param1": "value1"}
    )
    plan = await capability.plan(context)
    assert plan.capability_name == "provision_<resource>"
    assert len(plan.resources) > 0
```

## Best Practices

### 1. Plan-Then-Execute Pattern
Always generate a plan before executing. This allows:
- User review and approval
- Cost estimation
- Resource validation
- Dry-run testing

### 2. Idempotency
Capabilities should be idempotent where possible:
- Check if resources already exist
- Update vs create logic
- Avoid duplicate deployments

### 3. Cost Transparency
Always provide cost estimates in the plan:
- Monthly recurring costs
- One-time deployment costs
- Cost breakdown by resource type

### 4. Error Handling
Provide clear, actionable error messages:
- What went wrong
- Why it failed
- How to fix it
- Rollback options

### 5. Progress Reporting
For long-running deployments:
- Report progress milestones
- Estimated time remaining
- Current step information

### 6. Resource Outputs
Return useful outputs from execute():
- Resource URLs (dashboards, endpoints)
- Resource IDs (for later reference)
- Access credentials (securely)
- Connection strings

## Current Capabilities

### Databricks (`capabilities/databricks/`)
Provisions Azure Databricks infrastructure as a complete unit.

**What it deploys (together)**:
1. **Azure Resource Group** - Container for all resources
2. **Azure Databricks Workspace** - The Databricks service in Azure Portal
3. **Databricks Cluster** - Compute cluster inside the workspace

**Features**:
- Workspace provisioning (Standard/Premium SKU)
- Auto-scaling cluster creation
- GPU/CPU instance selection based on workload
- Cost optimization
- Smart naming conventions

**Parameters**:
- `team`: Team name (required)
- `environment`: dev/staging/prod (required)
- `region`: Azure region (required)
- `workspace_name`: Custom name (optional)

**Outputs**:
- Workspace URL
- Workspace ID
- Resource group name

**Cost**: ~$784-3600/month depending on configuration

**Implementation Note**: This capability contains all deployment logic in a 3-layer architecture (core/models/provisioning). See `capabilities/databricks/README.md` for details.

---

## Scope for This Spike

**Current**: Single capability (Databricks deployment)
**Future**: Could add more capabilities, but not planned for this spike

The architecture supports adding new capabilities, but for this POC we're focused on demonstrating the orchestrator pattern with one working capability.

---

## Future Capabilities (Examples Only - Not Implementing)

### Azure OpenAI (`capabilities/openai/`)
Provision Azure OpenAI service with model deployments.

### Firewall (`capabilities/firewall/`)
Open firewall ports for specific services.

### Networking (`capabilities/networking/`)
Configure VNets, subnets, NSGs.

### Storage (`capabilities/storage/`)
Provision Azure Storage accounts.

### ML Workspace (`capabilities/mlworkspace/`)
Deploy Azure Machine Learning workspace.

---

**For questions**: See `/docs/ARCHITECTURE_EVOLUTION.md` for architecture details.
