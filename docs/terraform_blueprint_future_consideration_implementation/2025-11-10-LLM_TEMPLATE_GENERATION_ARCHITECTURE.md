# LLM Template Generation Architecture (Future Enhancement)

**Date**: November 10, 2025
**Status**: DEFERRED - Documented for future implementation
**Decision**: Build blueprint pattern first, add LLM generation only if usage data justifies it

---

## Executive Summary

This document describes the **Option 3: Hybrid Template + LLM Generation** architecture that was discussed but **deliberately deferred** for the current implementation phase.

**Why Deferred**:
- Current spike scope: Prove concept with single capability (Databricks) ✅
- No usage data yet showing need for LLM-generated resources
- Template-based approach working well (100% success rate)
- YAGNI principle: Build what we need now, not what we might need later

**When to Implement**:
- After adding 2nd capability (Azure OpenAI)
- After 50+ real-world deployments
- When usage data shows 20%+ requests fail due to missing templates
- When specific resources are requested 10+ times consistently

---

## The Architecture (Future)

### **Complete Flow**

```
┌─────────────────────────────────────────────────────────────────┐
│ PHASE 1: Intent Recognition (LLM - Semantic Understanding)      │
├─────────────────────────────────────────────────────────────────┤
│ User: "I need Databricks with Unity Catalog for ML team"        │
│   ↓                                                              │
│ IntentParser (LLM):                                              │
│   - capability: "databricks"                                     │
│   - workload: "ml"                                               │
│   - features: ["unity_catalog"]                                  │
│   - team: "ml-team"                                              │
│   - environment: "prod"                                          │
└─────────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────────┐
│ PHASE 2: Resource Planning (Deterministic Rule Engine)          │
├─────────────────────────────────────────────────────────────────┤
│ ResourcePlanner:                                                 │
│   Required Resources:                                            │
│     1. azurerm_resource_group                  [HAS TEMPLATE ✓] │
│     2. azurerm_databricks_workspace            [HAS TEMPLATE ✓] │
│     3. databricks_cluster                      [HAS TEMPLATE ✓] │
│     4. databricks_metastore_assignment         [NO TEMPLATE ✗]  │
│                                                                  │
│   Decision:                                                      │
│     - Use templates for #1, #2, #3                               │
│     - Generate via LLM for #4                                    │
└─────────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────────┐
│ PHASE 3: Terraform Generation (Hybrid: Template + LLM)          │
├─────────────────────────────────────────────────────────────────┤
│ TerraformBuilder:                                                │
│                                                                  │
│   For each resource:                                             │
│     IF has_template(resource_type):                              │
│       ✓ Use template (fast, reliable)                            │
│     ELSE IF llm_supported(resource_type):                        │
│       ⚙️ Generate via LLM with validation                        │
│     ELSE:                                                        │
│       ⚠️ Generate via LLM, require user approval                 │
│                                                                  │
│   LLM Generation Pipeline:                                       │
│     1. LLM generates Terraform HCL                               │
│     2. Syntax validation (terraform validate)                    │
│     3. Schema validation (check against docs)                    │
│     4. User approval (if complex/experimental)                   │
└─────────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────────┐
│ PHASE 4: Semantic Validation (LLM Safety Check)                 │
├─────────────────────────────────────────────────────────────────┤
│ SemanticValidator (LLM):                                         │
│   • Does plan match user intent?                                 │
│   • Are resources configured correctly?                          │
│   • Any security/cost red flags?                                 │
│   • Missing required information?                                │
│                                                                  │
│   Result: APPROVED | APPROVED_WITH_QUESTIONS | CONCERNS | REJECTED │
└─────────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────────┐
│ PHASE 5: User Review & Approval                                 │
└─────────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────────┐
│ PHASE 6: Execution (Terraform Apply)                            │
└─────────────────────────────────────────────────────────────────┘
```

---

## Key Components (Future Implementation)

### **1. Resource Catalog**

```python
class ResourceCatalog:
    """Registry of available templates and LLM-supported resources"""

    # Resources we have battle-tested templates for
    TEMPLATE_RESOURCES = {
        "azurerm_resource_group": "templates/shared/resource_group.tf.j2",
        "azurerm_databricks_workspace": "templates/shared/workspace.tf.j2",
        "databricks_cluster": "templates/compute/cluster.tf.j2",
        "databricks_instance_pool": "templates/compute/instance_pool.tf.j2",
    }

    # Resources LLM can generate reliably (with validation)
    LLM_SUPPORTED_RESOURCES = {
        "databricks_metastore_assignment",
        "databricks_workspace_conf",
        "databricks_permissions",
        "databricks_secret_scope",
    }

    def can_generate(self, resource_type: str) -> tuple[str, str]:
        """Check if we can generate this resource and how"""
        if resource_type in self.TEMPLATE_RESOURCES:
            return ("template", self.TEMPLATE_RESOURCES[resource_type])
        elif resource_type in self.LLM_SUPPORTED_RESOURCES:
            return ("llm", None)
        else:
            return ("unknown", None)
```

### **2. LLM Terraform Generator**

```python
class LLMTerraformGenerator:
    """Generates Terraform via LLM with multi-stage validation"""

    async def generate_with_validation(
        self,
        resource_type: str,
        config: dict,
        require_user_approval: bool = False
    ) -> str:
        """Generate Terraform with validation pipeline"""

        # Stage 1: LLM generates Terraform
        tf_code = await self._generate(resource_type, config)

        # Stage 2: Syntax validation (terraform validate)
        syntax_valid = await self._validate_syntax(tf_code)
        if not syntax_valid.valid:
            tf_code = await self._fix_syntax_errors(tf_code, syntax_valid.errors)

        # Stage 3: Schema validation (check against Terraform docs)
        schema_valid = await self._validate_schema(resource_type, tf_code)
        if not schema_valid.valid:
            tf_code = await self._fix_schema_issues(tf_code, schema_valid.issues)

        # Stage 4: User approval for experimental resources
        if require_user_approval:
            approved = await self._get_user_approval(resource_type, tf_code)
            if not approved:
                raise UserRejectedError(f"User rejected {resource_type}")

        return tf_code
```

### **3. Semantic Validator**

```python
class SemanticValidator:
    """Final LLM check before execution"""

    async def validate_plan(
        self,
        original_request: InfrastructureRequest,
        generated_plan: CapabilityPlan
    ) -> SemanticValidation:
        """LLM reviews complete plan for semantic correctness"""

        prompt = f"""
        You are validating an infrastructure deployment plan.

        USER'S ORIGINAL REQUEST:
        {original_request.to_natural_language()}

        GENERATED PLAN:
        {generated_plan.terraform_code}

        VALIDATION CHECKLIST:
        1. Intent Match: Does this achieve what user asked for?
        2. Resource Completeness: All necessary resources included?
        3. Configuration Correctness: Resources configured properly?
        4. Security/Compliance: Any red flags?
        5. Cost Reasonableness: Appropriate for use case?
        6. Missing Information: Any required info missing?

        Respond: APPROVED | APPROVED_WITH_QUESTIONS | CONCERNS | REJECTED
        """

        response = await self.llm.generate(prompt, response_format="json")
        return SemanticValidation.from_json(response)
```

---

## Benefits (When Implemented)

✅ **Flexibility**: Handle resources we don't have templates for
✅ **Scalability**: Don't need templates for every possible resource
✅ **Safety**: Multi-stage validation prevents errors
✅ **Transparency**: User sees and approves generated code
✅ **Learning**: Track what gets generated to prioritize templates

---

## Risks & Mitigation

| Risk | Mitigation |
|------|------------|
| LLM generates invalid Terraform | Multi-stage validation (syntax, schema, semantic) |
| Non-deterministic output | Template-first approach (only use LLM when needed) |
| Cost increase (more API calls) | Cache validated resources, batch validation |
| Slower deployments | Async validation, parallel processing |
| User confusion | Clear labeling (template vs generated) |

---

## Implementation Triggers

Implement this architecture when:

1. **Usage Data Shows Need**
   - 20%+ of requests fail due to missing templates
   - Specific resource requested 10+ times
   - Multiple teams asking for same edge case

2. **Multi-Capability Deployed**
   - At least 2 capabilities in production
   - Pattern of template gaps identified
   - Resource catalog architecture stable

3. **Business Justification**
   - Cost of building < Cost of manual work
   - Clear ROI on flexibility vs complexity
   - User feedback demands it

---

## Current Alternative: Blueprint Pattern

Instead of LLM generation, we're implementing **blueprint pattern**:
- Curated patterns for common use cases
- Graceful failure for unsupported features
- User request tracking for prioritization
- Evidence-based template additions

**See**: `2025-11-10-BLUEPRINT_PATTERN_DESIGN.md` for current approach

---

## Decision Record

**Decision**: Defer LLM template generation until data justifies it

**Rationale**:
1. Current scope: Single capability, proven working
2. Templates sufficient for 80%+ of expected use cases
3. No evidence yet of template gaps
4. Simpler approach = lower risk, faster delivery
5. Can add later without architectural changes

**Revisit**: After Phase 2 (multi-capability) with real usage data

---

## References

- Architecture discussion: November 10, 2025 conversation
- Current implementation: See `CURRENT_STATE.md`
- Blueprint pattern: See `2025-11-10-BLUEPRINT_PATTERN_DESIGN.md`
