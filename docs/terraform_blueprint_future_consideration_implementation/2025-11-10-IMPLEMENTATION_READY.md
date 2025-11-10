# Blueprint Pattern Implementation - Ready to Execute

**Date**: November 10, 2025
**Status**: ✅ APPROVED - Ready for implementation
**Approach**: Modular templates + Blueprint pattern

---

## What's Been Approved

✅ **Blueprint Pattern Design** - 3 scenarios with graceful degradation
✅ **Modular Template Architecture** - Composable infrastructure modules
✅ **Implementation Plan Updated** - Includes template modularization
✅ **Feature Request Tracking** - Data-driven prioritization

---

## Key Design Decisions

### **1. Modular Templates (Approved)**

```
capabilities/databricks/templates/
├── core/
│   ├── resource_group.tf.j2      # Always needed
│   └── workspace.tf.j2            # Always needed
├── compute/
│   ├── instance_pool.tf.j2       # For pre-warmed compute
│   └── interactive_cluster.tf.j2 # For interactive/dev work
└── supporting/
    ├── variables.tf.j2
    ├── outputs.tf.j2              # Dynamic based on resources
    ├── provider.tf.j2
    └── terraform.tfvars.tf.j2
```

**Why**: Mix and match resources per blueprint (Lego block approach)

### **2. Blueprint Composition**

```python
Blueprint("databricks-ml-dev").resources = [
    "core/resource_group.tf.j2",
    "core/workspace.tf.j2",
    "compute/interactive_cluster.tf.j2"
]

Blueprint("databricks-ml-prod").resources = [
    "core/resource_group.tf.j2",
    "core/workspace.tf.j2",
    "compute/instance_pool.tf.j2"  # Different compute pattern
]
```

**Why**: Same modules, different combinations per use case

### **3. Three Scenarios**

- **Scenario 1**: Exact match → Full automation
- **Scenario 2**: No match → Graceful failure, show alternatives
- **Scenario 3**: Partial match → Deploy what we can, guide manual steps

**Why**: User-friendly degradation, always offers value

---

## Implementation Phases

### **Phase 0: Template Modularization** (NEW)
- Split monolithic `main.tf.j2` into modules
- Update `TerraformGenerator` for composition
- Backward compatibility maintained

### **Phase 1: Data Structures**
- Blueprint models (name, resources, metadata)
- BlueprintMatch (matching result)
- FeatureRequest (tracking)

### **Phase 2: Core Logic**
- BlueprintMatcher (find best match)
- FeatureRequestTracker (log unsupported)
- Integration with DatabricksCapability

### **Phase 3: User Experience**
- Update response formatting
- Clear messages for each scenario
- Feature request visibility

### **Phase 4-6: Testing, Docs, Rollout**
- Comprehensive tests
- Documentation updates
- Release v0.3.0

---

## What Gets Built

### **New Files** (11 total)

```
capabilities/databricks/
├── models/
│   └── blueprints.py                      # NEW: Data models
├── blueprints/
│   ├── __init__.py                        # NEW
│   └── library.py                         # NEW: Blueprint definitions
├── core/
│   ├── blueprint_matcher.py               # NEW: Matching logic
│   └── feature_tracker.py                 # NEW: Request tracking
└── templates/                             # NEW DIRECTORY
    ├── core/
    │   ├── resource_group.tf.j2           # NEW: Split from main.tf.j2
    │   └── workspace.tf.j2                # NEW: Split from main.tf.j2
    ├── compute/
    │   ├── instance_pool.tf.j2            # NEW: Extracted
    │   └── interactive_cluster.tf.j2      # NEW: Uncommented & extracted
    └── supporting/
        ├── variables.tf.j2                # MOVED from /templates
        ├── outputs.tf.j2                  # MOVED + dynamic logic
        ├── provider.tf.j2                 # MOVED from /templates
        └── terraform.tfvars.j2            # MOVED from /templates

tests/
├── test_blueprint_pattern.py              # NEW: Unit tests
└── test_blueprint_integration.py          # NEW: Integration tests
```

### **Modified Files** (4 total)

```
capabilities/databricks/
├── capability.py                          # MODIFIED: Blueprint integration
└── provisioning/terraform/
    └── generator.py                       # MODIFIED: Modular composition

capabilities/base.py                       # MODIFIED: CapabilityPlan fields
orchestrator/orchestrator_agent.py         # MODIFIED: Response formatting
```

### **Removed/Deprecated Files** (1)

```
templates/                                 # DEPRECATED (move to capability)
├── main.tf.j2                            # Will be split into modules
├── variables.tf.j2                       # Move to supporting/
├── outputs.tf.j2                         # Move to supporting/
├── provider.tf.j2                        # Move to supporting/
└── terraform.tfvars.j2                   # Move to supporting/
```

---

## Example: How It Works

### **User Request**
```
"I need Databricks for ML development with GPUs"
```

### **System Flow**
```
1. IntentParser → workload_type="ml", enable_gpu=True

2. BlueprintMatcher → Finds "databricks-ml-dev" (exact match)
   Resources: ["core/resource_group.tf.j2",
               "core/workspace.tf.j2",
               "compute/interactive_cluster.tf.j2"]

3. DecisionMaker → instance_type="Standard_NC6s_v3" (GPU)

4. TerraformGenerator.generate_from_resources()
   - Read resource_group.tf.j2 → render → HCL block 1
   - Read workspace.tf.j2 → render → HCL block 2
   - Read interactive_cluster.tf.j2 → render → HCL block 3
   - Combine into main.tf
   - Generate dynamic outputs (workspace_url, cluster_id, etc.)

5. TerraformExecutor → Deploy all 3 resources

6. Result: ✅ ML workspace with GPU cluster in 15 minutes
```

---

## Benefits

✅ **Composability**: Mix and match infrastructure modules
✅ **Maintainability**: Each module is small and focused
✅ **Scalability**: Easy to add new blueprints (just list modules)
✅ **User-Friendly**: Graceful degradation for unsupported cases
✅ **Data-Driven**: Track requests to prioritize features
✅ **Backward Compatible**: Existing tests keep working

---

## Timeline

**Estimated**: 3-4 days

- **Day 1**: Phase 0 (template modularization) + Phase 1 (data structures)
- **Day 2**: Phase 2 (integration) + Phase 3 (UX)
- **Day 3**: Phase 4 (testing) + Phase 5 (docs)
- **Day 4**: Buffer + rollout

---

## Risk Mitigation

| Risk | Mitigation |
|------|------------|
| Breaking existing functionality | Comprehensive test suite, backward compatibility |
| Template syntax errors | Validate each module independently |
| Blueprint matching failures | Extensive test scenarios |
| Feature tracking data loss | JSON validation, error handling |

---

## Success Criteria

- ✅ All 94 existing tests pass
- ✅ 20+ new tests added (unit + integration)
- ✅ All 3 scenarios work end-to-end
- ✅ Modular templates compose correctly
- ✅ Feature tracking persists
- ✅ Clear user messages for each scenario
- ✅ No breaking changes to existing deployments

---

## Next Step: Implementation

**Ready to proceed with implementation?**

The plan is complete, modular approach is designed, and all scenarios are covered.

**Start implementation**: Create feature branch and begin Phase 0 (template modularization)

---

## Questions Before Starting?

Review checklist:
- [ ] Modular template structure makes sense
- [ ] Blueprint composition approach is clear
- [ ] Three scenarios cover all cases
- [ ] Feature tracking approach is sufficient
- [ ] Testing strategy is comprehensive
- [ ] Timeline is reasonable

**If everything looks good, implementation can begin!** 🚀
