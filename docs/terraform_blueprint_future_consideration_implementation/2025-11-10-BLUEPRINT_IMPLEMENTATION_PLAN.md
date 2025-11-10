# Blueprint Pattern Implementation Plan

**Date**: November 10, 2025
**Status**: PLANNING PHASE - Awaiting approval
**Target**: Implement blueprint pattern with graceful degradation

---

## Overview

This document provides step-by-step implementation plan for the blueprint pattern designed in `2025-11-10-BLUEPRINT_PATTERN_DESIGN.md`.

**Estimated Effort**: 3-4 days
**Risk Level**: Low-Medium (template refactoring + new features)

**UPDATE**: User approved **MODULAR template approach**. This plan includes:
1. Blueprint pattern implementation (scenarios 1-3)
2. **Template modularization** (split monolithic → composable modules)
3. Feature request tracking
4. Comprehensive testing

---

## Phase 0: Template Modularization (NEW)

### **Step 0.1: Analyze Current Template**

**Current State**: `/templates/main.tf.j2` contains:
- Resource Group (always needed)
- Databricks Workspace (always needed)
- Instance Pool (for some use cases)
- Cluster (commented out, for other use cases)

**Target State**: Split into modular templates

```
capabilities/databricks/templates/
├── core/
│   ├── resource_group.tf.j2      # Always needed
│   └── workspace.tf.j2            # Always needed
├── compute/
│   ├── instance_pool.tf.j2       # For pre-warmed compute
│   └── interactive_cluster.tf.j2 # For interactive/dev work
└── supporting/
    ├── variables.tf.j2            # Moved from project root
    ├── outputs.tf.j2              # Moved from project root
    ├── provider.tf.j2             # Moved from project root
    └── terraform.tfvars.j2        # Moved from project root
```

---

### **Step 0.2: Create Modular Template Files**

#### **A. Core Templates (Always Needed)**

**File**: `capabilities/databricks/templates/core/resource_group.tf.j2` (NEW)

```jinja
# Azure Resource Group
resource "azurerm_resource_group" "main" {
  name     = var.resource_group_name
  location = var.region
  tags     = var.tags
}
```

**File**: `capabilities/databricks/templates/core/workspace.tf.j2` (NEW)

```jinja
# Databricks Workspace
resource "azurerm_databricks_workspace" "main" {
  name                = var.workspace_name
  resource_group_name = azurerm_resource_group.main.name
  location            = azurerm_resource_group.main.location
  sku                 = var.databricks_sku

  tags = merge(
    var.tags,
    {
      Name = var.workspace_name
    }
  )
}
```

#### **B. Compute Templates (Conditional)**

**File**: `capabilities/databricks/templates/compute/instance_pool.tf.j2` (NEW)

```jinja
# Databricks Instance Pool - Pre-warmed compute instances
resource "databricks_instance_pool" "main" {
  instance_pool_name = "${var.workspace_name}-pool"
  min_idle_instances = 0
  max_capacity       = 2

  node_type_id = var.worker_instance_type

  idle_instance_autotermination_minutes = 10

  preloaded_spark_versions = [
    var.spark_version
  ]

  azure_attributes {
    availability       = "ON_DEMAND_AZURE"
    spot_bid_max_price = -1
  }

  depends_on = [azurerm_databricks_workspace.main]
}
```

**File**: `capabilities/databricks/templates/compute/interactive_cluster.tf.j2` (NEW)

```jinja
# Interactive Databricks Cluster for development/notebooks
resource "databricks_cluster" "main" {
  cluster_name            = "${var.workspace_name}-cluster"
  spark_version           = var.spark_version
  node_type_id            = var.worker_instance_type
  driver_node_type_id     = var.driver_instance_type
  autotermination_minutes = var.autotermination_minutes

  autoscale {
    min_workers = var.min_workers
    max_workers = var.max_workers
  }

  azure_attributes {
    availability       = "ON_DEMAND_AZURE"
    first_on_demand    = 1
    spot_bid_max_price = -1
  }

  spark_conf = {
    "spark.databricks.cluster.profile" = "serverless"
    "spark.databricks.repl.allowedLanguages" = "python,sql,scala,r"
  }

  custom_tags = {
    ResourceClass = "Databricks"
    ClusterType   = "Interactive"
  }

  depends_on = [azurerm_databricks_workspace.main]
}
```

#### **C. Move Supporting Files**

Move these from `/templates/` to `capabilities/databricks/templates/supporting/`:
- `variables.tf.j2` (no changes)
- `outputs.tf.j2` (update to be dynamic based on resources)
- `provider.tf.j2` (no changes)
- `terraform.tfvars.j2` (no changes)

---

### **Step 0.3: Update TerraformGenerator for Modular Composition**

**File**: `capabilities/databricks/provisioning/terraform/generator.py` (MAJOR UPDATE)

**Current**: Generates from single template
**New**: Composes from multiple template modules

```python
class TerraformGenerator:
    """Generates Terraform HCL from modular templates"""

    def __init__(self, templates_dir: str | Path | None = None):
        if templates_dir is None:
            # Point to modular template directory
            project_root = Path(__file__).parent.parent.parent.parent.parent
            templates_dir = project_root / "capabilities" / "databricks" / "templates"
        else:
            templates_dir = Path(templates_dir)

        if not templates_dir.exists():
            raise FileNotFoundError(f"Templates directory not found: {templates_dir}")

        self.templates_dir = templates_dir
        self.env = Environment(
            loader=FileSystemLoader(str(templates_dir)),
            trim_blocks=True,
            lstrip_blocks=True,
            keep_trailing_newline=True,
        )

        logger.info(f"TerraformGenerator initialized with templates from: {templates_dir}")

    def generate_from_resources(
        self,
        resource_list: List[str],
        decision: InfrastructureDecision,
        environment: str = "prod",
        workload_type: str = "data_engineering",
        team: str = "infrastructure",
    ) -> TerraformFiles:
        """
        Generate Terraform by composing multiple resource templates.

        Args:
            resource_list: List of template paths (e.g., ["core/resource_group.tf.j2", ...])
            decision: Infrastructure decision with config details
            environment: Environment name for tagging
            workload_type: Workload type for tagging
            team: Team name for tagging

        Returns:
            TerraformFiles with composed main.tf
        """
        logger.info(f"Generating Terraform from {len(resource_list)} resource templates")

        # Prepare context
        context = {
            "workspace_name": decision.workspace_name,
            "resource_group_name": decision.resource_group_name,
            "region": decision.region,
            "databricks_sku": decision.databricks_sku,
            "min_workers": decision.min_workers,
            "max_workers": decision.max_workers,
            "driver_instance_type": decision.driver_instance_type,
            "worker_instance_type": decision.worker_instance_type,
            "spark_version": decision.spark_version,
            "autotermination_minutes": decision.autotermination_minutes,
            "enable_gpu": decision.enable_gpu,
            "estimated_monthly_cost": f"{decision.estimated_monthly_cost:.2f}",
            "environment": environment,
            "workload_type": workload_type,
            "team": team,
        }

        # Render each resource template
        resource_blocks = []
        for template_path in resource_list:
            logger.debug(f"Rendering template: {template_path}")
            try:
                rendered = self._render_template(template_path, context)
                resource_blocks.append(rendered)
            except TemplateNotFound:
                logger.error(f"Template not found: {template_path}")
                raise

        # Combine all resources into main.tf
        main_tf = "\n\n".join(resource_blocks)

        # Generate supporting files
        variables_tf = self._render_template("supporting/variables.tf.j2", context)
        outputs_tf = self._generate_dynamic_outputs(resource_list, context)
        terraform_tfvars = self._render_template("supporting/terraform.tfvars.j2", context)
        provider_tf = self._render_template("supporting/provider.tf.j2", context)

        logger.info("Successfully generated all Terraform files")

        return TerraformFiles(
            main_tf=main_tf,
            variables_tf=variables_tf,
            outputs_tf=outputs_tf,
            terraform_tfvars=terraform_tfvars,
            provider_tf=provider_tf,
        )

    def _generate_dynamic_outputs(self, resource_list: List[str], context: dict) -> str:
        """Generate outputs based on which resources are included"""

        outputs = []

        # Always include workspace outputs
        if "core/workspace.tf.j2" in resource_list:
            outputs.append("""
output "workspace_url" {
  description = "URL of the Databricks workspace"
  value       = "https://${azurerm_databricks_workspace.main.workspace_url}"
}

output "workspace_id" {
  description = "Azure resource ID of the Databricks workspace"
  value       = azurerm_databricks_workspace.main.id
}
""")

        # Add resource group outputs
        if "core/resource_group.tf.j2" in resource_list:
            outputs.append("""
output "resource_group_name" {
  description = "Name of the resource group"
  value       = azurerm_resource_group.main.name
}
""")

        # Add instance pool outputs if included
        if "compute/instance_pool.tf.j2" in resource_list:
            outputs.append("""
output "instance_pool_id" {
  description = "ID of the Databricks Instance Pool"
  value       = databricks_instance_pool.main.id
}
""")

        # Add cluster outputs if included
        if "compute/interactive_cluster.tf.j2" in resource_list:
            outputs.append("""
output "cluster_id" {
  description = "ID of the interactive cluster"
  value       = databricks_cluster.main.id
}
""")

        return "\n".join(outputs)

    # Keep existing generate() method for backward compatibility
    def generate(
        self,
        decision: InfrastructureDecision,
        environment: str = "prod",
        workload_type: str = "data_engineering",
        team: str = "infrastructure",
    ) -> TerraformFiles:
        """
        DEPRECATED: Use generate_from_resources() instead.
        Kept for backward compatibility with existing tests.
        """
        # Default to basic workspace with instance pool
        default_resources = [
            "core/resource_group.tf.j2",
            "core/workspace.tf.j2",
            "compute/instance_pool.tf.j2",
        ]

        return self.generate_from_resources(
            resource_list=default_resources,
            decision=decision,
            environment=environment,
            workload_type=workload_type,
            team=team,
        )
```

**Testing**:
- Unit test: Generate from single module
- Unit test: Generate from multiple modules
- Unit test: Dynamic outputs generation
- Integration test: End-to-end with blueprint
- Integration test: Backward compatibility with existing tests

---

## Phase 1: Data Structures & Core Components

### **Step 1.1: Create Blueprint Data Models**

**File**: `capabilities/databricks/models/blueprints.py` (NEW)

**What to create**:
```python
from dataclasses import dataclass
from typing import Set, Optional, List
from datetime import datetime

@dataclass
class Blueprint:
    """Curated infrastructure pattern"""
    name: str
    display_name: str
    description: str
    resources: List[str]
    workload_types: Set[str]
    environments: Set[str]
    required_features: Set[str]
    optional_features: Set[str]
    complexity: str  # "simple" | "moderate" | "complex"
    estimated_time_minutes: int
    estimated_monthly_cost_range: tuple[int, int]
    fully_supported: bool
    partial_support_notes: Optional[str] = None

@dataclass
class BlueprintMatch:
    """Result of matching request to blueprint"""
    match_type: str  # "exact" | "partial" | "none"
    confidence: float
    blueprint: Optional[Blueprint]
    supported_features: Set[str]
    unsupported_features: Set[str]
    manual_steps_required: List[str]
    alternative_blueprints: List[Blueprint]
    feature_requests_to_log: List[str]

@dataclass
class FeatureRequest:
    """Track unsupported feature requests"""
    feature_name: str
    requested_by: str
    requested_at: datetime
    context: str
    blueprint_attempted: str
    count: int = 1
```

**Testing**:
- Unit test: Create blueprints, verify fields
- Unit test: BlueprintMatch with various scenarios

---

### **Step 1.2: Define Blueprint Library**

**File**: `capabilities/databricks/blueprints/library.py` (NEW)

**What to create**:
```python
from ..models.blueprints import Blueprint

DATABRICKS_BLUEPRINTS = {
    "databricks-basic": Blueprint(
        name="databricks-basic",
        display_name="Basic Workspace",
        description="Empty workspace for exploration",
        resources=[
            "core/resource_group.tf.j2",
            "core/workspace.tf.j2",
        ],
        workload_types={"exploration", "learning", "testing"},
        environments={"dev", "sandbox"},
        required_features=set(),
        optional_features={"notebooks"},
        complexity="simple",
        estimated_time_minutes=10,
        estimated_monthly_cost_range=(200, 500),
        fully_supported=True,
    ),

    "databricks-ml-dev": Blueprint(
        name="databricks-ml-dev",
        display_name="ML Development Workspace",
        description="Interactive workspace for ML/DS teams with GPU support",
        resources=[
            "core/resource_group.tf.j2",
            "core/workspace.tf.j2",
            "compute/interactive_cluster.tf.j2",
        ],
        workload_types={"ml", "data_science", "analytics"},
        environments={"dev", "staging"},
        required_features={"interactive_compute"},
        optional_features={"gpu", "notebooks", "storage"},
        complexity="moderate",
        estimated_time_minutes=15,
        estimated_monthly_cost_range=(1000, 5000),
        fully_supported=True,
    ),

    "databricks-ml-prod": Blueprint(
        name="databricks-ml-prod",
        display_name="ML Production Jobs",
        description="Production workspace with instance pools for job execution",
        resources=[
            "core/resource_group.tf.j2",
            "core/workspace.tf.j2",
            "compute/instance_pool.tf.j2",
        ],
        workload_types={"ml", "data_engineering"},
        environments={"prod"},
        required_features={"job_compute", "autoscaling"},
        optional_features={"gpu"},
        complexity="moderate",
        estimated_time_minutes=15,
        estimated_monthly_cost_range=(3000, 10000),
        fully_supported=True,
    ),

    # Add more as needed...
}

# NOTE: resources list contains MODULAR template paths
# These will be composed by TerraformGenerator.generate_from_resources()

KNOWN_UNSUPPORTED_FEATURES = {
    "unity_catalog": "Centralized data governance",
    "private_endpoints": "Private network connectivity",
    "custom_vnet": "Custom virtual network configuration",
    "repos_integration": "Git integration for notebooks",
    "mlflow_model_serving": "MLflow model deployment",
    # Add more as discovered...
}
```

**Testing**:
- Unit test: All blueprints are valid
- Unit test: No duplicate blueprint names
- Integration test: Blueprints match expected structure

---

### **Step 1.3: Create Blueprint Matcher**

**File**: `capabilities/databricks/core/blueprint_matcher.py` (NEW)

**What to create**:
```python
import logging
from typing import Set
from ..models.blueprints import Blueprint, BlueprintMatch
from ..models.schemas import InfrastructureRequest

logger = logging.getLogger(__name__)

class BlueprintMatcher:
    """Matches user requests to available blueprints"""

    def __init__(self, blueprints: dict[str, Blueprint]):
        self.blueprints = blueprints
        logger.info(f"BlueprintMatcher initialized with {len(blueprints)} blueprints")

    def find_match(self, request: InfrastructureRequest) -> BlueprintMatch:
        """Find best matching blueprint for request"""

        # Extract features from request
        requested_features = self._extract_features(request)

        # Find candidates
        candidates = []
        for blueprint in self.blueprints.values():
            score = self._calculate_match_score(blueprint, request, requested_features)
            if score > 0:
                candidates.append((score, blueprint))

        if not candidates:
            return self._no_match_result(requested_features)

        # Sort by score
        candidates.sort(reverse=True, key=lambda x: x[0])
        best_score, best_blueprint = candidates[0]

        # Analyze support
        blueprint_features = best_blueprint.required_features | best_blueprint.optional_features
        supported = requested_features & blueprint_features
        unsupported = requested_features - blueprint_features

        # Determine match type
        if not unsupported and best_score > 0.8:
            match_type = "exact"
        elif unsupported:
            match_type = "partial"
        else:
            match_type = "close"

        logger.info(
            f"Match found: {best_blueprint.name} "
            f"(type={match_type}, score={best_score:.2f}, "
            f"unsupported={len(unsupported)})"
        )

        return BlueprintMatch(
            match_type=match_type,
            confidence=best_score,
            blueprint=best_blueprint,
            supported_features=supported,
            unsupported_features=unsupported,
            manual_steps_required=self._generate_manual_steps(unsupported),
            alternative_blueprints=[bp for _, bp in candidates[1:3]],
            feature_requests_to_log=list(unsupported),
        )

    def _extract_features(self, request: InfrastructureRequest) -> Set[str]:
        """Extract features from request"""
        features = set()

        if request.enable_gpu:
            features.add("gpu")

        # Parse additional requirements
        if request.additional_requirements:
            req_lower = request.additional_requirements.lower()
            if "unity catalog" in req_lower:
                features.add("unity_catalog")
            if "private endpoint" in req_lower:
                features.add("private_endpoints")
            if "custom" in req_lower and "vnet" in req_lower:
                features.add("custom_vnet")
            # Add more feature detection...

        return features

    def _calculate_match_score(
        self,
        blueprint: Blueprint,
        request: InfrastructureRequest,
        requested_features: Set[str]
    ) -> float:
        """Calculate match score (0.0 - 1.0)"""
        score = 0.0

        # Workload type (40%)
        if request.workload_type in blueprint.workload_types:
            score += 0.4

        # Environment (30%)
        if request.environment in blueprint.environments:
            score += 0.3

        # Feature overlap (30%)
        if requested_features:
            blueprint_features = blueprint.required_features | blueprint.optional_features
            overlap = len(requested_features & blueprint_features)
            feature_score = overlap / len(requested_features)
            score += 0.3 * feature_score
        else:
            score += 0.3

        return score

    def _generate_manual_steps(self, unsupported: Set[str]) -> List[str]:
        """Generate manual step descriptions"""
        from ..blueprints.library import KNOWN_UNSUPPORTED_FEATURES

        steps = []
        for feature in unsupported:
            description = KNOWN_UNSUPPORTED_FEATURES.get(
                feature,
                f"Configure {feature} manually"
            )
            steps.append(f"{feature}: {description}")

        return steps

    def _no_match_result(self, requested_features: Set[str]) -> BlueprintMatch:
        """Return result when no blueprint matches"""
        return BlueprintMatch(
            match_type="none",
            confidence=0.0,
            blueprint=None,
            supported_features=set(),
            unsupported_features=requested_features,
            manual_steps_required=[],
            alternative_blueprints=list(self.blueprints.values()),
            feature_requests_to_log=list(requested_features),
        )
```

**Testing**:
- Unit test: Exact match (workload + env + features all match)
- Unit test: Partial match (some features unsupported)
- Unit test: No match (no suitable blueprint)
- Unit test: Feature extraction from requests
- Unit test: Match score calculation

---

### **Step 1.4: Create Feature Request Tracker**

**File**: `capabilities/databricks/core/feature_tracker.py` (NEW)

**What to create**:
```python
import json
import logging
from pathlib import Path
from datetime import datetime
from typing import List, Tuple
from ..models.blueprints import FeatureRequest

logger = logging.getLogger(__name__)

class FeatureRequestTracker:
    """Track and analyze unsupported feature requests"""

    def __init__(self, storage_path: str = "feature_requests.json"):
        self.storage_path = Path(storage_path)
        self.requests: dict[str, List[FeatureRequest]] = self._load()

    def log_request(
        self,
        feature: str,
        user: str,
        context: str,
        blueprint: str
    ):
        """Log a feature request"""

        request = FeatureRequest(
            feature_name=feature,
            requested_by=user,
            requested_at=datetime.now(),
            context=context,
            blueprint_attempted=blueprint,
        )

        if feature not in self.requests:
            self.requests[feature] = []

        self.requests[feature].append(request)
        self._save()

        count = len(self.requests[feature])
        logger.info(f"Feature request logged: {feature} (count: {count})")

        # Alert if threshold reached
        if count == 10:
            logger.warning(
                f"⚠️ Feature '{feature}' has reached 10 requests! "
                "Consider prioritizing for automation."
            )

    def get_top_requests(self, limit: int = 10) -> List[Tuple[str, int]]:
        """Get most requested features"""
        counts = {
            feature: len(requests)
            for feature, requests in self.requests.items()
        }
        return sorted(
            counts.items(),
            key=lambda x: x[1],
            reverse=True
        )[:limit]

    def get_request_count(self, feature: str) -> int:
        """Get count for specific feature"""
        return len(self.requests.get(feature, []))

    def should_prioritize(self, feature: str, threshold: int = 10) -> bool:
        """Check if feature should be prioritized"""
        return self.get_request_count(feature) >= threshold

    def _load(self) -> dict[str, List[FeatureRequest]]:
        """Load from storage"""
        if not self.storage_path.exists():
            return {}

        try:
            with open(self.storage_path) as f:
                data = json.load(f)

            # Convert to FeatureRequest objects
            result = {}
            for feature, requests in data.items():
                result[feature] = [
                    FeatureRequest(
                        feature_name=r["feature_name"],
                        requested_by=r["requested_by"],
                        requested_at=datetime.fromisoformat(r["requested_at"]),
                        context=r["context"],
                        blueprint_attempted=r["blueprint_attempted"],
                    )
                    for r in requests
                ]
            return result

        except Exception as e:
            logger.error(f"Error loading feature requests: {e}")
            return {}

    def _save(self):
        """Save to storage"""
        try:
            # Convert to JSON-serializable format
            data = {}
            for feature, requests in self.requests.items():
                data[feature] = [
                    {
                        "feature_name": r.feature_name,
                        "requested_by": r.requested_by,
                        "requested_at": r.requested_at.isoformat(),
                        "context": r.context,
                        "blueprint_attempted": r.blueprint_attempted,
                    }
                    for r in requests
                ]

            with open(self.storage_path, 'w') as f:
                json.dump(data, f, indent=2)

        except Exception as e:
            logger.error(f"Error saving feature requests: {e}")
```

**Testing**:
- Unit test: Log requests, verify count
- Unit test: Get top requests
- Unit test: Persistence (save/load)
- Unit test: Prioritization threshold

---

## Phase 2: Integration with Capability

### **Step 2.1: Update DatabricksCapability**

**File**: `capabilities/databricks/capability.py` (MODIFY)

**Changes needed**:

1. Import new components:
```python
from .blueprints.library import DATABRICKS_BLUEPRINTS
from .core.blueprint_matcher import BlueprintMatcher
from .core.feature_tracker import FeatureRequestTracker
```

2. Initialize in `__init__`:
```python
def __init__(self):
    # Existing...
    self.intent_parser = IntentParser()
    self.decision_maker = DecisionMaker()
    # ...

    # NEW: Blueprint pattern
    self.blueprints = DATABRICKS_BLUEPRINTS
    self.blueprint_matcher = BlueprintMatcher(self.blueprints)
    self.feature_tracker = FeatureRequestTracker()
```

3. Update `plan()` method:
```python
async def plan(self, context: CapabilityContext) -> CapabilityPlan:
    """Generate plan using blueprint matching"""

    # Parse intent (existing)
    request = await self.intent_parser.parse(context.parameters)

    # NEW: Find matching blueprint
    match = self.blueprint_matcher.find_match(request)

    # NEW: Handle based on match type
    if match.match_type == "exact":
        return await self._plan_supported(request, match)
    elif match.match_type in ["partial", "close"]:
        return await self._plan_partial(request, match)
    else:
        return await self._plan_unsupported(request, match)
```

4. Add new private methods with modular template composition:
```python
async def _plan_supported(
    self,
    request: InfrastructureRequest,
    match: BlueprintMatch
) -> CapabilityPlan:
    """Full automation path (Scenario 1)"""
    logger.info(f"✅ Full support via blueprint: {match.blueprint.name}")

    # Make configuration decisions (existing)
    decision = self.decision_maker.make_decision(request)

    # NEW: Generate Terraform from blueprint's modular resources
    terraform_files = self.terraform_generator.generate_from_resources(
        resource_list=match.blueprint.resources,  # e.g., ["core/resource_group.tf.j2", "core/workspace.tf.j2", ...]
        decision=decision,
        environment=request.environment,
        workload_type=request.workload_type,
        team=request.team,
    )

    return CapabilityPlan(
        status="ready",
        blueprint_name=match.blueprint.name,
        terraform_files=terraform_files,
        resources=[r.replace(".tf.j2", "") for r in match.blueprint.resources],
        estimated_cost=decision.estimated_monthly_cost,
        estimated_time_minutes=match.blueprint.estimated_time_minutes,
        requires_approval=False,
        message=f"✅ I can fully automate this using the '{match.blueprint.display_name}' pattern.",
    )

async def _plan_partial(
    self,
    request: InfrastructureRequest,
    match: BlueprintMatch
) -> CapabilityPlan:
    """Partial support path (Scenario 3)"""
    # Generate base infrastructure
    # Log unsupported features
    # Add manual step guidance

async def _plan_unsupported(
    self,
    request: InfrastructureRequest,
    match: BlueprintMatch
) -> CapabilityPlan:
    """Unsupported path (Scenario 2)"""
    # Log feature requests
    # Show available blueprints
    # Offer alternatives
```

**Testing**:
- Integration test: Scenario 1 (exact match)
- Integration test: Scenario 2 (unsupported)
- Integration test: Scenario 3 (partial)
- Integration test: Feature tracking works

---

### **Step 2.2: Update CapabilityPlan Model**

**File**: `capabilities/base.py` (MODIFY)

**Add new fields to CapabilityPlan**:
```python
@dataclass
class CapabilityPlan:
    # Existing fields...
    resources: list[str]
    estimated_cost: float
    terraform_files: Optional[TerraformFiles] = None

    # NEW: Blueprint pattern fields
    blueprint_name: Optional[str] = None
    match_type: Optional[str] = None  # "exact" | "partial" | "none"
    manual_steps: Optional[List[str]] = None
    alternative_blueprints: Optional[List[str]] = None
    user_message: Optional[str] = None  # Message to display to user
```

---

## Phase 3: User Experience & Output

### **Step 3.1: Update Orchestrator Response Formatting**

**File**: `orchestrator/orchestrator_agent.py` (MODIFY)

**Update how plans are presented to user**:

```python
def _format_capability_plan(self, plan: CapabilityPlan) -> str:
    """Format plan for user with blueprint context"""

    if plan.match_type == "exact":
        return f"""
✅ I can fully automate this using the '{plan.blueprint_name}' pattern.

Resources to deploy:
{self._format_resources(plan.resources)}

Estimated time: {plan.estimated_time_minutes} minutes
Estimated cost: ${plan.estimated_cost}/month

Shall I proceed?
"""

    elif plan.match_type == "partial":
        return f"""
🤝 I can partially automate this using '{plan.blueprint_name}'.

I'll deploy automatically:
{self._format_resources(plan.supported_resources)}

You'll need to configure manually:
{self._format_manual_steps(plan.manual_steps)}

Estimated time:
- Automated: {plan.estimated_time_minutes} minutes
- Manual steps: 30-60 minutes

I've logged these features for future automation.

Proceed with automated part?
"""

    else:  # unsupported
        return f"""
⚠️ I don't currently support fully automated provisioning for this.

Available patterns:
{self._format_alternative_blueprints(plan.alternative_blueprints)}

Your requested features have been logged for prioritization.

Would you like to use one of the available patterns instead?
"""
```

---

## Phase 4: Testing Strategy

### **Unit Tests** (NEW)

Create: `tests/test_blueprint_pattern.py`

```python
def test_blueprint_exact_match():
    """Test exact blueprint match"""

def test_blueprint_partial_match():
    """Test partial match with unsupported features"""

def test_blueprint_no_match():
    """Test no matching blueprint"""

def test_feature_tracker():
    """Test feature request tracking"""

def test_blueprint_matcher_scoring():
    """Test match score calculation"""
```

### **Integration Tests** (NEW)

Create: `tests/test_blueprint_integration.py`

```python
async def test_scenario_1_full_support():
    """Test end-to-end with fully supported pattern"""

async def test_scenario_2_unsupported():
    """Test graceful handling of unsupported request"""

async def test_scenario_3_partial():
    """Test partial automation with manual steps"""

async def test_feature_request_logging():
    """Test feature requests are logged correctly"""
```

---

## Phase 5: Documentation

### **Step 5.1: Update User Documentation**

**File**: `capabilities/databricks/README.md` (UPDATE)

Add section:
```markdown
## Supported Patterns

We currently support these Databricks patterns:

### 1. Basic Workspace
For exploration and learning...

### 2. ML Development
For ML/DS teams with interactive compute...

### 3. ML Production
For production ML jobs...

### 4. SQL Analytics
For BI and analytics workloads...

### 5. Streaming
For real-time data processing...

## Requesting New Features

If you need something not listed above, the agent will:
1. Deploy what it can automatically
2. Provide guidance for manual steps
3. Log your feature request for prioritization

When 10+ users request the same feature, we prioritize automation.
```

---

## Phase 6: Rollout Plan

### **Step 6.1: Internal Testing**

1. Run full test suite
2. Test each scenario manually with CLI
3. Verify feature tracking works
4. Check all error messages are user-friendly

### **Step 6.2: Documentation Review**

1. Ensure all new code has docstrings
2. Update README.md
3. Update .github/copilot-instructions.md

### **Step 6.3: Deployment**

1. Merge to main branch
2. Tag release: `v0.2.0-blueprint-pattern`
3. Update CURRENT_STATE.md

---

## File Changes Summary

### New Files (7)
1. `capabilities/databricks/models/blueprints.py` - Data models
2. `capabilities/databricks/blueprints/__init__.py` - Package init
3. `capabilities/databricks/blueprints/library.py` - Blueprint definitions
4. `capabilities/databricks/core/blueprint_matcher.py` - Matching logic
5. `capabilities/databricks/core/feature_tracker.py` - Request tracking
6. `tests/test_blueprint_pattern.py` - Unit tests
7. `tests/test_blueprint_integration.py` - Integration tests

### Modified Files (4)
1. `capabilities/databricks/capability.py` - Add blueprint logic
2. `capabilities/base.py` - Update CapabilityPlan model
3. `orchestrator/orchestrator_agent.py` - Update response formatting
4. `capabilities/databricks/README.md` - Document supported patterns

### Generated Files (1)
1. `feature_requests.json` - Runtime feature tracking data

---

## Risk Assessment

| Risk | Likelihood | Impact | Mitigation |
|------|-----------|--------|------------|
| Breaking existing functionality | Low | High | Comprehensive tests, gradual rollout |
| User confusion with new messages | Medium | Medium | Clear messaging, examples |
| Feature tracker file corruption | Low | Low | JSON validation, error handling |
| Blueprint definitions incomplete | Medium | Medium | Start with core patterns, iterate |

---

## Success Criteria

- ✅ All existing tests pass
- ✅ New tests achieve >90% coverage
- ✅ All 3 scenarios work end-to-end
- ✅ Feature tracking persists correctly
- ✅ User messages are clear and helpful
- ✅ No breaking changes to existing deployments

---

## Timeline

**Day 1**:
- Phase 1: Data structures and core components
- Initial testing

**Day 2**:
- Phase 2: Integration with capability
- Phase 3: User experience updates
- Comprehensive testing

**Day 3**:
- Phase 4-5: Testing and documentation
- Phase 6: Rollout

---

## Approval Checklist

Before proceeding, confirm:
- [ ] Design document reviewed and approved
- [ ] Data structures make sense
- [ ] Three scenarios cover all cases
- [ ] Graceful degradation is appropriate
- [ ] Feature tracking approach is acceptable
- [ ] Testing strategy is sufficient
- [ ] Implementation timeline is reasonable

---

## Next Steps After Approval

1. Create feature branch: `feature/blueprint-pattern`
2. Implement Phase 1 (data structures)
3. Write tests for Phase 1
4. Implement Phase 2 (integration)
5. Write tests for Phase 2
6. Complete remaining phases
7. Full test suite run
8. Code review
9. Merge to main

---

## Modular Template Flow Summary

### **Complete End-to-End Example**

**User Request**: "I need Databricks for ML development"

```
Step 1: Intent Parsing
└─> InfrastructureRequest(workload_type="ml", environment="dev", enable_gpu=True)

Step 2: Blueprint Matching
└─> BlueprintMatch(
      blueprint="databricks-ml-dev",
      resources=["core/resource_group.tf.j2",
                 "core/workspace.tf.j2",
                 "compute/interactive_cluster.tf.j2"]
    )

Step 3: Configuration Decisions
└─> InfrastructureDecision(
      workspace_name="ml-team-dev",
      databricks_sku="premium",
      worker_instance_type="Standard_NC6s_v3",  # GPU
      ...
    )

Step 4: Modular Template Composition
└─> TerraformGenerator.generate_from_resources(
      resource_list=[
        "core/resource_group.tf.j2",           # Module 1
        "core/workspace.tf.j2",                # Module 2
        "compute/interactive_cluster.tf.j2"    # Module 3
      ],
      decision=InfrastructureDecision(...)
    )

    For each template:
      1. Read template file
      2. Render with Jinja2 (replace {{variables}})
      3. Add to list

    Combine all rendered templates:
      main.tf = module1 + "\n\n" + module2 + "\n\n" + module3

Step 5: Dynamic Outputs Generation
└─> Based on which resources were included:
      - resource_group? → Add resource_group_name output
      - workspace? → Add workspace_url output
      - cluster? → Add cluster_id output

Step 6: Return Complete Terraform
└─> TerraformFiles(
      main.tf="""
        resource "azurerm_resource_group" "main" { ... }

        resource "azurerm_databricks_workspace" "main" { ... }

        resource "databricks_cluster" "main" { ... }
      """,
      variables.tf="...",
      outputs.tf="...",  # Dynamic based on resources
      provider.tf="...",
      terraform.tfvars="..."
    )

Step 7: Execute Deployment
└─> terraform apply → Deploys all 3 resources to Azure
```

### **Key Benefit: Composability**

Different blueprints, different resource combinations:

```python
# Blueprint 1: ML Development (interactive cluster)
Blueprint("databricks-ml-dev").resources = [
    "core/resource_group.tf.j2",
    "core/workspace.tf.j2",
    "compute/interactive_cluster.tf.j2"  # ← Interactive for notebooks
]

# Blueprint 2: ML Production (instance pool for jobs)
Blueprint("databricks-ml-prod").resources = [
    "core/resource_group.tf.j2",
    "core/workspace.tf.j2",
    "compute/instance_pool.tf.j2"        # ← Different compute pattern
]

# Blueprint 3: Basic Workspace (no compute)
Blueprint("databricks-basic").resources = [
    "core/resource_group.tf.j2",
    "core/workspace.tf.j2"               # ← Minimal setup
]

# Same modular templates, different combinations!
```

---

## Implementation Checklist

### **Phase 0: Template Modularization** ✓
- [ ] Create `capabilities/databricks/templates/core/` directory
- [ ] Create `capabilities/databricks/templates/compute/` directory
- [ ] Create `capabilities/databricks/templates/supporting/` directory
- [ ] Split `main.tf.j2` → `resource_group.tf.j2` + `workspace.tf.j2`
- [ ] Extract instance pool → `instance_pool.tf.j2`
- [ ] Uncomment + extract cluster → `interactive_cluster.tf.j2`
- [ ] Move supporting files to `supporting/`
- [ ] Update `TerraformGenerator` for modular composition
- [ ] Add `generate_from_resources()` method
- [ ] Add `_generate_dynamic_outputs()` method
- [ ] Keep backward-compatible `generate()` method
- [ ] Test modular generation

### **Phase 1: Data Structures** ✓
- [ ] Create `models/blueprints.py` with dataclasses
- [ ] Create `blueprints/library.py` with 3-5 blueprints (using modular paths)
- [ ] Create `core/blueprint_matcher.py`
- [ ] Create `core/feature_tracker.py`
- [ ] Test all components

### **Phase 2: Integration** ✓
- [ ] Update `capability.py` with blueprint logic
- [ ] Update `base.py` CapabilityPlan model
- [ ] Test scenarios 1, 2, 3
- [ ] Verify feature tracking works

### **Phase 3: User Experience** ✓
- [ ] Update orchestrator response formatting
- [ ] Add clear messages for each scenario
- [ ] Test conversation flow

### **Phase 4: Testing** ✓
- [ ] Unit tests for all new components
- [ ] Integration tests for 3 scenarios
- [ ] Test modular template composition
- [ ] Backward compatibility tests
- [ ] Full test suite (ensure 94 tests still pass)

### **Phase 5: Documentation** ✓
- [ ] Update `capabilities/databricks/README.md`
- [ ] Document supported blueprints
- [ ] Document modular template structure
- [ ] Update `.github/copilot-instructions.md`

### **Phase 6: Rollout** ✓
- [ ] Code review
- [ ] Merge to main
- [ ] Update `CURRENT_STATE.md`
- [ ] Tag release: `v0.3.0-blueprint-modular`

---

**This implementation plan has been updated with modular template approach as approved by user.**

Questions or concerns? Please review and provide feedback before implementation begins.

**Implementation will start after your explicit approval.** 👍
