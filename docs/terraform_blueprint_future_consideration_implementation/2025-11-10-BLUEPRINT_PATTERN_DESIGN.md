# Blueprint Pattern Design & Specification

**Date**: November 10, 2025
**Status**: DESIGN PHASE - Awaiting approval before implementation
**Purpose**: Define curated infrastructure patterns with graceful degradation for unsupported cases

---

## Executive Summary

The **Blueprint Pattern** provides a structured approach to handle three scenarios:

1. ✅ **Supported Patterns**: User requests something we can fully automate
2. ⚠️ **Unsupported Features**: User requests something we can't automate yet
3. 🤝 **Edge Cases**: User requests something partially supported

**Philosophy**: We're building an agent for **common use cases**, not a **complete Databricks replacement**. The blueprint pattern makes this explicit and handles it gracefully.

---

## The Three Scenarios

### **Scenario 1: User Asks for Something We Support** ✅

```
User: "I need a Databricks workspace for ML development"
    ↓
Agent: [Recognizes "ml-dev" pattern]
    ↓
Blueprint: "databricks-ml-dev"
    - Resource Group
    - Databricks Workspace (Premium SKU)
    - Interactive Cluster (GPU instances)
    ↓
Agent: "I can deploy this! Here's the plan..."
    [Shows cost, config, timeline]
    ↓
User: "Looks good, deploy it"
    ↓
Result: ✅ Deployed in 15 minutes
```

**Characteristics**:
- Fully automated
- High confidence
- Fast deployment
- Proven reliability

### **Scenario 2: User Asks for Something We DON'T Support** ⚠️

```
User: "I need Databricks with Unity Catalog and private endpoints"
    ↓
Agent: [Recognizes "unity_catalog", "private_endpoints"]
    ↓
Blueprint Check: Not supported (no template exists)
    ↓
Agent: "I currently support these Databricks patterns:
       1. ML Development (interactive clusters)
       2. Production Jobs (scheduled clusters)
       3. SQL Analytics (SQL warehouses)
       4. Streaming (Delta Live Tables)

       Unity Catalog and private endpoints aren't automated yet.

       I can:
       • Deploy the base workspace (15 min)
       • Generate Terraform with TODOs for Unity Catalog
       • Provide docs on configuring private endpoints manually

       Or I can note this request for future automation.

       Would you like to proceed with base workspace?"
    ↓
User: "Yes, deploy base and show me the TODOs"
    ↓
Agent: [Deploys base workspace]
       [Generates terraform with TODO comments]
       [Logs feature request: unity_catalog (count: 1)]
    ↓
Result: 🤝 Partial automation + clear next steps
```

**Characteristics**:
- Graceful degradation
- Clear explanation
- Partial automation offered
- Feature request tracked
- User keeps momentum

### **Scenario 3: User Asks for Edge Case** 🤔

```
User: "I need Databricks for ML but with custom VNet configuration
       for on-premises connectivity"
    ↓
Agent: [Recognizes "ml" pattern + "custom_vnet" requirement]
    ↓
Blueprint: "databricks-ml-dev" (closest match)
Additional Requirements: "custom_vnet" (advanced)
    ↓
Agent: "I can deploy the ML workspace, but custom VNet for on-prem
       connectivity requires additional configuration.

       I'll deploy:
       ✓ Resource Group
       ✓ Databricks Workspace
       ✓ ML Cluster

       You'll need to configure:
       ⚠️ Custom VNet (I'll create the VNet resource, you configure peering)
       ⚠️ On-premises connectivity (requires VPN/ExpressRoute setup)

       Estimated time:
       - Automated: 15 minutes
       - Manual config: 30-60 minutes (depending on network setup)

       Proceed with automated part?"
    ↓
User: "Yes"
    ↓
Agent: [Deploys standard resources]
       [Creates VNet with TODO comments]
       [Provides detailed guide for manual steps]
       [Logs feature request: custom_vnet_onprem (count: 1)]
    ↓
Result: 🤝 Accelerated deployment + guided manual steps
```

**Characteristics**:
- Recognizes supported parts
- Identifies manual requirements
- Sets clear expectations
- Provides guidance
- Still saves time

---

## Architecture

### **Data Structures**

```python
from dataclasses import dataclass
from typing import List, Set, Optional

@dataclass
class Blueprint:
    """A curated infrastructure pattern"""

    # Identification
    name: str                           # "databricks-ml-dev"
    display_name: str                   # "ML Development Workspace"
    description: str                    # "Interactive workspace for ML/DS teams"

    # Resources
    resources: List[str]                # ["resource_group", "workspace", "cluster"]

    # Matching criteria
    workload_types: Set[str]            # {"ml", "data_science"}
    environments: Set[str]              # {"dev", "staging"}
    required_features: Set[str]         # {"interactive_compute"}
    optional_features: Set[str]         # {"notebooks", "storage"}

    # Metadata
    complexity: str                     # "simple" | "moderate" | "complex"
    estimated_time_minutes: int         # 15
    estimated_monthly_cost_range: tuple # (1000, 3000)

    # Support status
    fully_supported: bool               # True
    partial_support_notes: Optional[str] # None


@dataclass
class FeatureRequest:
    """Track requests for unsupported features"""

    feature_name: str                   # "unity_catalog"
    requested_by: str                   # "ml-team"
    requested_at: datetime
    context: str                        # "Need centralized governance"
    blueprint_attempted: str            # "databricks-ml-dev"
    count: int = 1                      # Number of times requested


@dataclass
class BlueprintMatch:
    """Result of matching user request to blueprint"""

    # Match quality
    match_type: str                     # "exact" | "partial" | "none"
    confidence: float                   # 0.0 - 1.0

    # Matched blueprint (if any)
    blueprint: Optional[Blueprint]

    # Analysis
    supported_features: Set[str]        # Features we can handle
    unsupported_features: Set[str]      # Features we can't handle
    manual_steps_required: List[str]    # What user must do manually

    # Recommendations
    alternative_blueprints: List[Blueprint]  # Other options
    feature_requests_to_log: List[str]       # Track for future
```

### **Blueprint Library**

```python
# capabilities/databricks/blueprints.py

DATABRICKS_BLUEPRINTS = {
    "databricks-basic": Blueprint(
        name="databricks-basic",
        display_name="Basic Workspace",
        description="Empty workspace for exploration and learning",
        resources=["resource_group", "workspace"],
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
        description="Interactive workspace for ML/data science teams with GPU support",
        resources=["resource_group", "workspace", "interactive_cluster"],
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
        description="Production workspace with job clusters and instance pools",
        resources=["resource_group", "workspace", "instance_pool", "job_cluster"],
        workload_types={"ml", "data_engineering"},
        environments={"prod"},
        required_features={"job_compute", "autoscaling"},
        optional_features={"gpu"},
        complexity="moderate",
        estimated_time_minutes=15,
        estimated_monthly_cost_range=(3000, 10000),
        fully_supported=True,
    ),

    "databricks-sql": Blueprint(
        name="databricks-sql",
        display_name="SQL Analytics Workspace",
        description="Workspace optimized for SQL analytics and BI workloads",
        resources=["resource_group", "workspace", "sql_warehouse"],
        workload_types={"analytics", "bi", "reporting"},
        environments={"dev", "staging", "prod"},
        required_features={"sql_compute"},
        optional_features=set(),
        complexity="moderate",
        estimated_time_minutes=15,
        estimated_monthly_cost_range=(2000, 8000),
        fully_supported=True,
    ),

    "databricks-streaming": Blueprint(
        name="databricks-streaming",
        display_name="Streaming Pipeline",
        description="Real-time data processing with Delta Live Tables",
        resources=["resource_group", "workspace", "dlt_pipeline"],
        workload_types={"streaming", "real_time", "data_engineering"},
        environments={"dev", "staging", "prod"},
        required_features={"streaming_compute", "delta_tables"},
        optional_features=set(),
        complexity="complex",
        estimated_time_minutes=20,
        estimated_monthly_cost_range=(4000, 15000),
        fully_supported=True,
    ),
}

# Features we know about but don't support yet
KNOWN_UNSUPPORTED_FEATURES = {
    "unity_catalog": "Centralized data governance and access control",
    "private_endpoints": "Private network connectivity",
    "custom_vnet": "Custom virtual network configuration",
    "repos_integration": "Git integration for notebooks",
    "custom_rbac": "Advanced role-based access control",
    "mlflow_model_serving": "MLflow model deployment endpoints",
    "custom_init_scripts": "Custom initialization scripts",
    "secret_scopes": "Secret management integration",
}
```

### **Blueprint Matcher**

```python
class BlueprintMatcher:
    """Matches user requests to blueprints"""

    def __init__(self, blueprints: dict[str, Blueprint]):
        self.blueprints = blueprints

    def find_match(
        self,
        request: InfrastructureRequest
    ) -> BlueprintMatch:
        """Find the best blueprint match for a request"""

        # Extract features from request
        requested_features = self._extract_features(request)

        # Find matching blueprints
        candidates = []
        for blueprint in self.blueprints.values():
            score = self._calculate_match_score(blueprint, request)
            if score > 0:
                candidates.append((score, blueprint))

        if not candidates:
            return self._no_match_result(requested_features)

        # Best match
        candidates.sort(reverse=True, key=lambda x: x[0])
        best_score, best_blueprint = candidates[0]

        # Analyze supported vs unsupported
        supported = requested_features & (
            best_blueprint.required_features | best_blueprint.optional_features
        )
        unsupported = requested_features - supported

        # Determine match type
        if not unsupported and best_score > 0.8:
            match_type = "exact"
        elif unsupported:
            match_type = "partial"
        else:
            match_type = "close"

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

    def _calculate_match_score(
        self,
        blueprint: Blueprint,
        request: InfrastructureRequest
    ) -> float:
        """Calculate how well blueprint matches request (0.0 - 1.0)"""
        score = 0.0

        # Workload type match (40% weight)
        if request.workload_type in blueprint.workload_types:
            score += 0.4

        # Environment match (30% weight)
        if request.environment in blueprint.environments:
            score += 0.3

        # Feature overlap (30% weight)
        requested_features = self._extract_features(request)
        blueprint_features = blueprint.required_features | blueprint.optional_features

        if requested_features:
            overlap = len(requested_features & blueprint_features)
            feature_score = overlap / len(requested_features)
            score += 0.3 * feature_score
        else:
            score += 0.3  # No special features = default match

        return score
```

### **Feature Request Tracker**

```python
class FeatureRequestTracker:
    """Track and analyze unsupported feature requests"""

    def __init__(self, storage_path: str = "feature_requests.json"):
        self.storage_path = storage_path
        self.requests: dict[str, list[FeatureRequest]] = self._load()

    def log_request(self, feature: str, user: str, context: str, blueprint: str):
        """Log a request for an unsupported feature"""

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

        logger.info(
            f"Feature request logged: {feature} "
            f"(total requests: {len(self.requests[feature])})"
        )

    def get_top_requests(self, limit: int = 10) -> list[tuple[str, int]]:
        """Get most requested features"""
        counts = {
            feature: len(requests)
            for feature, requests in self.requests.items()
        }
        return sorted(counts.items(), key=lambda x: x[1], reverse=True)[:limit]

    def should_prioritize(self, feature: str, threshold: int = 10) -> bool:
        """Check if feature has enough requests to prioritize"""
        return len(self.requests.get(feature, [])) >= threshold
```

---

## Decision Flow

```python
class DatabricksCapability(BaseCapability):
    """Updated capability with blueprint pattern"""

    def __init__(self):
        self.blueprints = DATABRICKS_BLUEPRINTS
        self.matcher = BlueprintMatcher(self.blueprints)
        self.feature_tracker = FeatureRequestTracker()
        # ... existing components

    async def plan(self, context: CapabilityContext) -> CapabilityPlan:
        """Generate plan using blueprint matching"""

        # Parse intent
        request = await self.intent_parser.parse(context.parameters)

        # Find matching blueprint
        match = self.matcher.find_match(request)

        # Handle based on match type
        if match.match_type == "exact":
            # Scenario 1: Full support
            return await self._plan_supported(request, match)

        elif match.match_type == "partial":
            # Scenario 3: Edge case (partial support)
            return await self._plan_partial(request, match)

        else:
            # Scenario 2: Unsupported
            return await self._plan_unsupported(request, match)

    async def _plan_supported(
        self,
        request: InfrastructureRequest,
        match: BlueprintMatch
    ) -> CapabilityPlan:
        """Full automation path"""

        logger.info(f"✅ Full support via blueprint: {match.blueprint.name}")

        # Standard decision making
        decision = self.decision_maker.make_decision(request)

        # Generate Terraform from blueprint
        terraform = self.terraform_generator.generate(decision)

        return CapabilityPlan(
            status="ready",
            blueprint_name=match.blueprint.name,
            terraform_code=terraform,
            estimated_time=match.blueprint.estimated_time_minutes,
            requires_approval=False,
            message=f"✅ I can fully automate this using the '{match.blueprint.display_name}' pattern.",
        )

    async def _plan_partial(
        self,
        request: InfrastructureRequest,
        match: BlueprintMatch
    ) -> CapabilityPlan:
        """Partial automation with manual steps"""

        logger.info(
            f"🤝 Partial support: {match.blueprint.name} + "
            f"{len(match.unsupported_features)} manual steps"
        )

        # Log unsupported features
        for feature in match.feature_requests_to_log:
            self.feature_tracker.log_request(
                feature=feature,
                user=request.team,
                context=request.additional_requirements or "",
                blueprint=match.blueprint.name,
            )

        # Generate base infrastructure
        decision = self.decision_maker.make_decision(request)
        terraform = self.terraform_generator.generate(decision)

        # Add TODO comments for manual steps
        terraform_with_todos = self._add_manual_step_comments(
            terraform,
            match.manual_steps_required
        )

        message = f"""
        🤝 I can partially automate this using '{match.blueprint.display_name}'.

        I'll deploy:
        {self._format_supported_features(match.supported_features)}

        You'll need to configure manually:
        {self._format_unsupported_features(match.unsupported_features)}

        Estimated time:
        - Automated: {match.blueprint.estimated_time_minutes} minutes
        - Manual steps: 30-60 minutes (see generated Terraform TODOs)

        I've logged these features for future automation:
        {self._format_feature_requests(match.feature_requests_to_log)}
        """

        return CapabilityPlan(
            status="partial_support",
            blueprint_name=match.blueprint.name,
            terraform_code=terraform_with_todos,
            estimated_time=match.blueprint.estimated_time_minutes,
            requires_approval=True,  # User should review manual steps
            message=message,
            manual_steps=match.manual_steps_required,
        )

    async def _plan_unsupported(
        self,
        request: InfrastructureRequest,
        match: BlueprintMatch
    ) -> CapabilityPlan:
        """No automation available"""

        logger.info(f"⚠️ Unsupported request: {match.unsupported_features}")

        # Log all requested features
        for feature in match.feature_requests_to_log:
            self.feature_tracker.log_request(
                feature=feature,
                user=request.team,
                context=request.additional_requirements or "",
                blueprint="none",
            )

        # Show what we CAN do
        supported_patterns = [
            f"{i}. {bp.display_name}: {bp.description}"
            for i, bp in enumerate(self.blueprints.values(), 1)
        ]

        message = f"""
        ⚠️ I don't currently support fully automated provisioning for this configuration.

        You requested:
        {self._format_unsupported_features(match.unsupported_features)}

        I currently support these Databricks patterns:
        {chr(10).join(supported_patterns)}

        Options:
        1. Choose one of the supported patterns above
        2. Deploy base workspace, then configure manually (I can guide you)
        3. Submit feature request for future automation

        These features have been logged. If 10+ users request the same feature,
        we'll prioritize automation.

        Current request counts:
        {self._format_feature_request_stats()}

        Would you like to proceed with a supported pattern?
        """

        return CapabilityPlan(
            status="unsupported",
            blueprint_name=None,
            terraform_code=None,
            estimated_time=0,
            requires_approval=False,
            message=message,
            alternative_blueprints=list(self.blueprints.values()),
        )
```

---

## Graceful Degradation Examples

### **Example 1: Unity Catalog (Unsupported)**

```python
User: "Deploy Databricks with Unity Catalog"

Agent Response:
"""
⚠️ Unity Catalog automation isn't available yet.

I can deploy:
✓ Base Databricks workspace (Premium SKU required for Unity Catalog)
✓ Resource group
✓ Default cluster

For Unity Catalog, you'll need to:
1. Enable Unity Catalog in workspace settings (10 min)
2. Create metastore (via UI or Terraform - I can provide template)
3. Assign metastore to workspace

Documentation: [link to Unity Catalog setup guide]

This feature has been requested 12 times and is prioritized for Q1 2026.

Proceed with base workspace? (yes/no)
"""
```

### **Example 2: Custom Networking (Partial Support)**

```python
User: "Deploy Databricks with VNet injection for on-prem connectivity"

Agent Response:
"""
🤝 I can partially automate this.

I'll deploy:
✓ Resource group
✓ Virtual network with required subnets
✓ Databricks workspace with VNet injection
✓ ML cluster

You'll need to configure:
⚠️ VPN Gateway or ExpressRoute (for on-prem connection)
⚠️ Route tables
⚠️ Firewall rules

Estimated time:
- Automated: 20 minutes
- Manual networking: 45-90 minutes

I'll generate Terraform with TODO comments for manual steps.

Proceed? (yes/no)
"""
```

---

## Benefits

1. ✅ **Clear Expectations**: Users know what's automated vs manual
2. ✅ **Graceful Failure**: No hard stops, always offers alternatives
3. ✅ **Data-Driven**: Track requests to prioritize features
4. ✅ **Maintainable**: Easy to add new blueprints
5. ✅ **Scalable**: Pattern works for any capability (Databricks, OpenAI, etc.)
6. ✅ **User-Friendly**: Reduces frustration with transparency

---

## Success Metrics

- **Coverage**: % of requests fully automated
- **Partial Automation**: % of requests with some automation
- **Feature Velocity**: Time from request to template creation
- **User Satisfaction**: Feedback on graceful degradation
- **Request Patterns**: Which features to prioritize next

---

## Next Steps

See: `2025-11-10-BLUEPRINT_IMPLEMENTATION_PLAN.md` for implementation details

---

## Approval Required

**This document requires review and approval before implementation begins.**

Please review:
1. Blueprint data structures
2. Three scenario handling
3. Graceful degradation approach
4. Feature request tracking

Feedback/questions welcome before proceeding to implementation.
