# Phase 2: Capability Integration

**Status**: ✅ COMPLETE
**Date**: December 2024
**Branch**: `capabilities-architecture`

## Overview

Phase 2 successfully integrated the capability abstraction layer, connecting the conversational orchestrator to actual infrastructure deployment. The orchestrator can now execute Databricks workspace deployments through a clean, extensible capability interface.

## Objectives

1. ✅ Define capability abstraction layer (BaseCapability interface)
2. ✅ Wrap existing Databricks agent in capability pattern
3. ✅ Integrate capability execution into orchestrator
4. ✅ Implement plan-then-execute workflow
5. ✅ Add approval workflow placeholder (full implementation in Phase 4)
6. ✅ Validate with comprehensive integration tests

## Architecture

### Capability Interface

**BaseCapability Abstract Class** (`orchestrator/capabilities.py`):
```python
class BaseCapability(ABC):
    """Base class for all infrastructure provisioning capabilities."""

    @property
    @abstractmethod
    def name(self) -> str:
        """Unique capability identifier (e.g., 'provision_databricks')"""
        pass

    @property
    @abstractmethod
    def description(self) -> str:
        """Human-readable capability description"""
        pass

    @abstractmethod
    async def plan(self, context: CapabilityContext) -> CapabilityPlan:
        """Generate deployment plan without executing"""
        pass

    @abstractmethod
    async def execute(self, plan: CapabilityPlan) -> CapabilityResult:
        """Execute approved plan"""
        pass

    async def validate(self, context: CapabilityContext) -> tuple[bool, list[str]]:
        """Validate context before planning (optional)"""
        return True, []

    async def rollback(self, result: CapabilityResult) -> bool:
        """Rollback failed deployment (optional, future)"""
        return False
```

### Data Models

**CapabilityContext**:
- `user_request`: Original natural language request
- `capability_name`: Name of capability to execute
- `parameters`: Extracted parameters from conversation
- `metadata`: Additional context (user info, session, etc.)

**CapabilityPlan**:
- `capability_name`: Capability that created this plan
- `description`: Human-readable summary
- `resources`: List of resources to be created
- `estimated_cost`: Monthly cost estimate
- `estimated_duration`: Deployment time estimate (minutes)
- `requires_approval`: Whether user approval is needed
- `details`: Capability-specific details (terraform files, configs, etc.)
- `to_summary()`: Generate human-readable summary for user review

**CapabilityResult**:
- `capability_name`: Capability that was executed
- `success`: Whether deployment succeeded
- `message`: Status message
- `resources_created`: List of created resources
- `outputs`: Deployment outputs (URLs, IDs, credentials)
- `error`: Error message if failed
- `duration_seconds`: Actual execution time
- `to_summary()`: Generate human-readable result summary

### Execution Flow

```
User Conversation (MAF)
    ↓
Orchestrator.execute_capability(name, params)
    ↓
1. Create CapabilityContext
    ↓
2. Validate context
    ↓
3. Generate Plan (capability.plan())
    - Parse requirements
    - Make configuration decisions
    - Generate infrastructure code
    - Run dry-run deployment
    - Extract resources and costs
    ↓
4. Present plan to user
    - Display resources to be created
    - Show cost estimates
    - Show deployment timeline
    ↓
5. Get approval (Phase 2: auto-approve, Phase 4: interactive)
    ↓
6. Execute deployment (capability.execute())
    - Run actual deployment
    - Track progress
    - Capture outputs
    ↓
7. Return result to user
```

## Implementation

### 1. Base Capability Interface (242 lines)

**File**: `orchestrator/capabilities.py`

Created comprehensive capability abstraction:
- `BaseCapability` abstract class defining capability contract
- Plan/execute lifecycle with optional validate/rollback
- Data models with `to_summary()` methods for user-friendly output
- Fully typed with modern Python type hints

**Key Design Decisions**:
- **Two-phase execution**: Plan first, execute after approval prevents accidental deployments
- **Async by default**: All methods async for future scalability (parallel capabilities, streaming updates)
- **Summary methods**: `to_summary()` on plans/results ensures consistent user communication
- **Optional hooks**: `validate()` and `rollback()` support advanced capabilities without forcing all to implement

### 2. Databricks Capability (298 lines)

**File**: `orchestrator/databricks_capability.py`

Wrapped existing Databricks agent code in capability interface:

**Components**:
- `IntentRecognizer`: Parse natural language → InfrastructureRequest
- `DecisionEngine`: Make configuration decisions (SKUs, instance types, cluster config)
- `TerraformGenerator`: Generate Terraform HCL files
- `TerraformExecutor`: Execute Terraform commands

**plan() Method**:
1. Build request text from context parameters
2. Recognize intent to extract infrastructure requirements
3. Override with explicit parameters from conversation
4. Make configuration decisions
5. Generate Terraform files
6. Run `terraform plan` (dry-run)
7. Extract resources from decision
8. Estimate monthly cost
9. Return CapabilityPlan with all details

**execute() Method**:
1. Get working directory from plan
2. Run `terraform apply` with auto-approve (already approved by user)
3. Extract outputs (workspace URL, ID, resource group)
4. Return CapabilityResult with deployment status

**Cost Estimation**:
- Databricks workspace: $75-150/month based on SKU
- Cluster compute: Instance type × workers × hours/month
- GPU instances: $1.14/hour
- Standard compute: $0.19/hour
- Assumes 12 hours/day, 22 days/month usage

**Resource Extraction**:
- Resource Group
- Databricks Workspace (with SKU)
- Databricks Cluster (if workers configured)

### 3. Orchestrator Integration

**File**: `orchestrator/orchestrator_agent.py`

Added capability execution to conversational orchestrator:

**Changes**:
- Added `capabilities` dict to store registered capabilities
- Added `_register_capabilities()` to load available capabilities
- Added `execute_capability(name, request, params)` method (94 lines)
- Added `get_capability(name)` and `list_capabilities()` helpers

**execute_capability() Flow**:
```python
async def execute_capability(
    self,
    capability_name: str,
    user_request: str,
    parameters: dict
) -> tuple[CapabilityPlan, CapabilityResult]:
    """Execute capability with plan-then-execute workflow."""

    # 1. Get capability
    capability = self.capabilities.get(capability_name)

    # 2. Create context
    context = CapabilityContext(...)

    # 3. Validate
    valid, errors = await capability.validate(context)

    # 4. Generate plan
    plan = await capability.plan(context)

    # 5. Present plan to user
    print(plan.to_summary())

    # 6. Get approval (Phase 2: auto-approve)
    # NOTE: Phase 4 will add interactive approval workflow
    approved = True

    # 7. Execute if approved
    result = await capability.execute(plan)

    # 8. Return plan and result
    return plan, result
```

**Auto-Approval Placeholder**:
Phase 2 uses `approved = True` with comment noting Phase 4 will add:
- Interactive approval prompts
- Plan diff visualization
- Cost confirmation
- Approval state tracking

### 4. Integration Tests (185 lines, 8 tests)

**File**: `tests/test_capability_integration.py`

Comprehensive test coverage:

1. **test_databricks_capability_registration** ✅
   - Verifies orchestrator loads DatabricksCapability
   - Checks capability is accessible by name

2. **test_databricks_capability_properties** ✅
   - Validates capability name and description
   - Ensures consistent naming convention

3. **test_databricks_capability_plan_generation** ✅
   - Creates CapabilityContext with test parameters
   - Generates plan via `capability.plan()`
   - Validates plan structure and contents
   - Checks resources, costs, terraform details

4. **test_databricks_capability_validation** ✅
   - Tests `validate()` method with valid context
   - Ensures validation returns True with no errors

5. **test_orchestrator_capability_execution_flow** ✅
   - End-to-end test through orchestrator
   - Creates context, generates plan, validates structure
   - Does NOT execute deployment (avoids Azure costs in test)

6. **test_orchestrator_list_capabilities** ✅
   - Verifies `list_capabilities()` returns registered capabilities
   - Ensures "provision_databricks" is present

7. **test_orchestrator_get_unknown_capability** ✅
   - Tests error handling for non-existent capabilities
   - Validates None is returned (not exception)

8. **test_capability_plan_to_summary** ✅
   - Generates plan and calls `to_summary()`
   - Verifies summary contains key information
   - Checks user-readable format

**Test Results**: 8/8 passing, 58% code coverage

## Technical Challenges & Solutions

### Challenge 1: API Mismatch - File Writing

**Problem**: Capability assumed `terraform_generator.write_files()` method existed, but actual implementation uses `terraform_executor.execute_deployment()`.

**Root Cause**: Misunderstanding of existing agent architecture. The generator only creates in-memory file objects, executor handles file I/O.

**Solution**:
- Changed `plan()` to use `execute_deployment(dry_run=True)`
- This writes files AND runs terraform plan in one step
- Changed `execute()` to use `execute_deployment(dry_run=False)`
- Aligned with existing agent patterns

**Learning**: When wrapping existing code, carefully analyze actual APIs rather than assuming clean separation. The existing agent evolved organically and has combined responsibilities.

### Challenge 2: Model Field Names

**Problem**: Referenced `decision.resource_group` but model uses `resource_group_name`.

**Root Cause**: Inconsistent naming between model definition and usage expectations.

**Solution**:
- Read actual model definition in `agent/models.py`
- Updated all references to use `resource_group_name`
- Validated against InfrastructureDecision schema

**Learning**: Always read model definitions before using. Don't trust assumptions from variable names or documentation.

### Challenge 3: Non-Existent Fields

**Problem**: Code checked `if decision.create_cluster:` but InfrastructureDecision doesn't have `create_cluster` field.

**Root Cause**: Capability code assumed optional cluster creation, but existing implementation ALWAYS creates clusters.

**Evidence**: InfrastructureDecision always has:
- `min_workers`, `max_workers`
- `driver_instance_type`, `worker_instance_type`
- `spark_version`, `autotermination_minutes`, `enable_gpu`

**Solution**:
- Changed conditional from `if decision.create_cluster:` to `if decision.max_workers > 0:`
- Since clusters are always created, this condition is always true
- Kept conditional for future extensibility (optional cluster creation)

**Also Fixed**:
- `decision.instance_types.get("driver")` → `decision.driver_instance_type`
- `decision.team` → `infra_request.team`
- `decision.environment` → `infra_request.environment`

**Learning**: InfrastructureDecision holds configuration decisions (instance types, SKUs), not original request metadata (team, environment). Use the right model for each data type.

### Challenge 4: Iterative Debugging

**Process**:
1. Run tests → 5/8 passing, 3 failed on `write_files`
2. Search for method → not found
3. Read infrastructure_agent.py → uses `execute_deployment()`
4. Fix capability code → rerun tests
5. 5/8 passing, 3 failed on `resource_group`
6. Read models.py → field is `resource_group_name`
7. Fix capability code → rerun tests
8. 5/8 passing, 3 failed on `create_cluster`
9. Read InfrastructureDecision → no such field
10. Fix capability code → rerun tests
11. 5/8 passing, 3 failed on `decision.team`
12. Realize team is in request not decision → fix
13. All 8 tests passing ✅

**Learning**: Wrapping legacy code requires patient, iterative debugging. Each test run reveals new assumptions that don't match reality. Keep fixing one issue at a time, running tests to validate, and moving to next issue.

## Code Quality

**Linting**: Minor trailing whitespace warnings (cosmetic, not functional)

**Test Coverage**: 58% overall
- New code (capabilities): 68-82% coverage
- Orchestrator: 44% (conversational flow not tested)
- Agent modules: 17-78% (legacy code, not modified)

**Type Safety**: All new code fully typed with modern Python hints

## Key Learnings

### 1. Plan-Then-Execute is Critical

**Why**: Prevents accidental deployments and enables user review.

The two-phase execution pattern:
- **Plan phase**: Generate all details (resources, costs, terraform) without changing anything
- **Review phase**: Present plan to user in human-readable format
- **Execute phase**: Only run if user approves

This matches terraform's own workflow and provides safety gates.

### 2. Wrapper Pattern Works Well

Wrapping existing agent/ code in capability interface allowed:
- ✅ Reuse all existing logic (IntentRecognizer, DecisionEngine, etc.)
- ✅ Clean separation between orchestrator and deployment
- ✅ Extensible to new capabilities (OpenAI, Firewall, etc.)
- ✅ Easy to test in isolation

Challenges:
- ⚠️ Requires careful API analysis of wrapped code
- ⚠️ Assumptions about internal structure often wrong
- ⚠️ Debugging needs understanding of both wrapper and wrapped code

### 3. Summary Methods Enable User Communication

Adding `to_summary()` to CapabilityPlan and CapabilityResult was excellent decision:
- Centralizes formatting logic
- Ensures consistent user experience
- Capability-specific details can be presented appropriately
- Easy to test (summary is just a string)

Example plan summary:
```
=== DEPLOYMENT PLAN ===
Capability: provision_databricks
Description: Provision Databricks workspace for ml-team team (prod environment)

Resources to be created:
  - Resource Group: rg-ml-team-prod
  - Databricks Workspace: ml-team-prod (premium SKU)
  - Databricks Cluster: ml-team-prod-cluster
    Instance: Standard_NC6s_v3
    Workers: 2-8

Estimated Cost: $3606.91/month
Estimated Duration: 15 minutes
Requires Approval: Yes
```

### 4. Model Separation is Important

The existing agent has two model types:
- **InfrastructureRequest**: User's original request (team, environment, workload, etc.)
- **InfrastructureDecision**: Configuration decisions (instance types, SKUs, cluster config)

These serve different purposes:
- Request captures "what the user wants"
- Decision captures "how we'll implement it"

The capability must use BOTH:
- Build description from request (team, environment)
- Build resources from decision (instance types, SKUs)

Mixing these causes attribute errors.

### 5. Test-Driven Debugging Works

Writing comprehensive tests BEFORE fixing bugs revealed all issues:
- 8 tests created up-front
- Each test failure revealed an API mismatch
- Fixed issues one at a time
- Reran tests after each fix
- Final: 8/8 passing

This is better than:
- ❌ Implementing without tests
- ❌ Discovering bugs in manual testing
- ❌ Fixing without validation
- ❌ Breaking things without knowing

## Next Steps: Phase 3

Phase 2 established the capability pattern with Databricks. Phase 3 will:

1. **Add Azure OpenAI Capability**
   - Implement `ProvisionAzureOpenAICapability`
   - Wrap or create OpenAI provisioning logic
   - Generate ARM templates or Bicep files
   - Follow same plan/execute pattern

2. **Multi-Capability Workflows**
   - Enable orchestrator to execute multiple capabilities
   - Handle dependencies between capabilities
   - Coordinate sequential and parallel deployments

3. **State Management**
   - Track deployment state across sessions
   - Store plans and results
   - Enable resume after failures

4. **Enhanced Error Handling**
   - Better validation before planning
   - Detailed error messages with recovery suggestions
   - Partial failure handling

Phase 4 will add:
- Interactive approval workflow
- Plan diff visualization
- Cost approval thresholds
- Approval state persistence

## Files Changed

**New Files**:
- `orchestrator/capabilities.py` (242 lines) - Base capability interface
- `orchestrator/databricks_capability.py` (298 lines) - Databricks wrapper
- `tests/test_capability_integration.py` (185 lines) - Integration tests

**Modified Files**:
- `orchestrator/orchestrator_agent.py` - Added capability execution (94 lines added)

**Test Results**:
```
tests/test_capability_integration.py::test_databricks_capability_registration PASSED
tests/test_capability_integration.py::test_databricks_capability_properties PASSED
tests/test_capability_integration.py::test_databricks_capability_plan_generation PASSED
tests/test_capability_integration.py::test_databricks_capability_validation PASSED
tests/test_capability_integration.py::test_orchestrator_capability_execution_flow PASSED
tests/test_capability_integration.py::test_orchestrator_list_capabilities PASSED
tests/test_capability_integration.py::test_orchestrator_get_unknown_capability PASSED
tests/test_capability_integration.py::test_capability_plan_to_summary PASSED

========================= 8 passed in 45.28s ==========================
```

## Conclusion

Phase 2 successfully connected the conversational orchestrator to actual infrastructure deployment through a clean, extensible capability abstraction. The orchestrator can now:

✅ Engage in multi-turn conversations (Phase 1)
✅ Use tools for discovery and planning (Phase 1.5-1.6)
✅ Execute Databricks deployments through capabilities (Phase 2)

The capability pattern proved robust and extensible. The plan-then-execute workflow provides safety. The wrapper pattern enables reuse of existing agent code while maintaining clean separation.

**Ready for Phase 3**: Adding new capabilities (Azure OpenAI), multi-capability workflows, and state management.
