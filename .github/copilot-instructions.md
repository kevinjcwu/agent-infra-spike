# GitHub Copilot Instructions for agent-infra-spike

## Project Overview
This is a spike/POC to build an AI agent that automates infrastructure provisioning using LLMs and modern agent frameworks. The agent takes natural language requests through multi-turn conversations and can deploy production-grade infrastructure in Azure.

**Current Focus**: Building a conversational orchestrator that routes requests to specialized infrastructure capabilities (Databricks, Azure OpenAI, etc.)

## Context Documents
- **Primary Reference**: `/docs/PRD.md` - Original product requirements and vision
- **Architecture**: `/docs/ARCHITECTURE_EVOLUTION.md` - Target architecture and design decisions
- **Implementation Status**: `/docs/implementation_status/` - Phase-by-phase progress and learnings

## Project Status

**Completed**:
- ✅ Phase 0: MAF (Microsoft Agent Framework) integration with Azure OpenAI
- ✅ Phase 1: Multi-turn conversational orchestrator with tool integration
- ✅ Phase 1.5: Tool Registry pattern for scalable tool management
- ✅ Phase 1.6: Capability Registry pattern for hallucination prevention
- ✅ Phase 2: Capability Integration - BaseCapability interface, DatabricksCapability
- ✅ Restructured to match architecture vision
- ✅ **November 10, 2025**: Databricks capability refactored to three-layer architecture

**Current Architecture**:
- `orchestrator/` - MAF-based conversational orchestrator (multi-turn, tool-enabled)
- `capabilities/` - Pluggable capability system (BaseCapability, Databricks with layered structure)
- `templates/` - Terraform templates for infrastructure deployment

**Architecture Principles**: See detailed principles below

**Scope**: Single capability (Databricks) with clean three-layer architecture:
- `core/` - Business logic (intent parsing, decisions, config)
- `models/` - Data structures (Pydantic schemas)
- `provisioning/` - Infrastructure deployment (Terraform generation/execution)

**Next**: Ready for adding 2nd capability (Azure OpenAI) following established pattern

## Code Generation Guidelines

### Language & Style
- **Language**: Python 3.12+
- **Style**: Follow PEP 8, modern type hints (dict/list not Dict/List)
- **Docstrings**: Google style
- **Error Handling**: Use custom exceptions with proper chaining (`raise ... from e`)
- **Testing**: Write pytest tests (use pytest-asyncio for async code)

### Current Tech Stack
*Note: These are current implementation choices. May evolve based on requirements.*

- **Agent Framework**: Microsoft Agent Framework (MAF) 1.0.0b251105
- **LLM**: Azure OpenAI GPT-4o (with function calling support)
- **Templating**: Jinja2 for Terraform generation
- **Infrastructure**: Terraform via subprocess
- **Validation**: Pydantic for data models
- **Testing**: pytest + pytest-asyncio + pytest-cov

**Why these choices**:
- MAF: Automatic conversation context, middleware support, Azure integration
- GPT-4o: Function calling, structured outputs, large context window
- Pydantic: Type safety, auto-validation, schema generation
- Terraform: Industry standard, provider ecosystem, state management

### Architecture Principles
1. **Separation of Concerns**: Each module has single responsibility
   - Orchestrator: Conversation management and capability routing
   - Tools: Specific helper functions (discovery, naming, cost estimation)
   - Capabilities: Infrastructure provisioning logic (Databricks, OpenAI, etc.)
   - Each capability is self-contained with its own config, models, and implementation

2. **Tool Registry Pattern**: Dynamic tool registration with decorators
   ```python
   @tool_manager.register("Tool description")
   def my_tool(param: str) -> str:
       return result
   ```
   - Auto-generates OpenAI function schemas from type hints
   - No hardcoded if/elif dispatch chains
   - Scales to hundreds of tools

3. **Capability Registry Pattern**: Prevent LLM hallucination with validation
   - Registry stores allowed infrastructure capabilities
   - LLM provides semantic understanding of user requests
   - Tool validates capability names against registry
   - Rejects hallucinated capabilities with clear errors
   - See: `orchestrator/capability_registry.py`

4. **MAF Conversation Management**: Framework handles context automatically
   - No manual conversation history tracking
   - Multi-turn conversations work out of box
   - Agent maintains state across user interactions

5. **Pluggable Capabilities**: All capabilities implement BaseCapability interface
   - Located in `capabilities/<capability-name>/`
   - Each capability: `__init__.py` + `capability.py`
   - Standard lifecycle: `plan()` → `validate()` → `execute()` → `rollback()`
   - See: `capabilities/base.py` for interface definition

### Adding New Capabilities

**When creating a new infrastructure capability:**

1. **Create directory structure**:
   ```
   capabilities/
   └── <capability-name>/
       ├── __init__.py          # Export main capability class
       └── capability.py        # Implement BaseCapability
   ```

2. **Implement BaseCapability interface**:
   ```python
   from capabilities.base import BaseCapability, CapabilityContext, CapabilityPlan, CapabilityResult

   class MyCapability(BaseCapability):
       @property
       def name(self) -> str:
           return "provision_<resource>"

       @property
       def description(self) -> str:
           return "Provision <resource> in Azure"

       async def plan(self, context: CapabilityContext) -> CapabilityPlan:
           """Generate deployment plan (dry-run)"""
           # Parse context.parameters
           # Make configuration decisions
           # Generate infrastructure code
           # Return plan with resources, costs, terraform details

       async def execute(self, plan: CapabilityPlan) -> CapabilityResult:
           """Execute approved plan"""
           # Deploy infrastructure
           # Return result with outputs
   ```

3. **Register in orchestrator**:
   ```python
   # In orchestrator/orchestrator_agent.py, _register_capabilities()
   from capabilities.<capability-name> import MyCapability

   self.capabilities["provision_<resource>"] = MyCapability()
   ```

4. **Add to capability registry**:
   ```python
   # In orchestrator/capability_registry.py
   capability_registry.register(
       name="provision_<resource>",
       description="Provision <resource> infrastructure",
       tags=["azure", "<category>"],
       required_params=["param1", "param2"],
       optional_params=["param3"]
   )
   ```

5. **Create tests**:
   ```
   tests/
   └── test_<capability>_integration.py  # Integration tests
   ```

**Example**: See `capabilities/databricks/` for reference implementation

### Scalability Principles

**Critical Design Rules** (Avoid future code smells):

1. **No Hardcoded Dispatch**: If you find yourself writing `if x == "a": ... elif x == "b": ...`
   - ❌ BAD: Hardcoded if/elif chains for routing (doesn't scale)
   - ✅ GOOD: Registry pattern with dynamic dispatch by name
   - **Why**: Adding the 100th item shouldn't require touching routing code

2. **No Manual Schema Duplication**: If you're copying type information between places
   - ❌ BAD: Define function signature, then separately define JSON schema
   - ✅ GOOD: Auto-generate schemas from type hints via introspection
   - **Why**: Single source of truth, reduces errors, less maintenance

3. **No Repetitive Pattern Code**: If you copy-paste similar code 3+ times
   - ❌ BAD: Copy-paste similar logic with minor variations
   - ✅ GOOD: Extract to reusable function, class, or decorator
   - **Why**: Bug fixes require one change, not N changes

4. **Prefer Discovery Over Registration**: Let code declare itself
   - ❌ BAD: Manually add new items to central registry file
   - ✅ GOOD: Decorator/import side-effects auto-register
   - **Why**: Adding new feature shouldn't require editing core files

**Before You Code, Ask**:
- "If we have 100 of these, will this pattern still work?"
- "Am I duplicating information that exists elsewhere?"
- "Will the next developer need to edit N files to add one feature?"

### File Organization
```
agent-infra-spike/
├── orchestrator/              # Conversational orchestrator
│   ├── __init__.py
│   ├── orchestrator_agent.py  # MAF-based conversation manager
│   ├── tool_manager.py        # Dynamic tool registration system
│   ├── capability_registry.py # Infrastructure capability validation
│   ├── tools.py               # Helper tools (capability selection, naming, cost)
│   └── models.py              # Data classes
│
├── capabilities/              # Pluggable infrastructure capabilities
│   ├── __init__.py            # Exports BaseCapability, data models
│   ├── base.py                # BaseCapability interface, CapabilityContext/Plan/Result
│   └── databricks/            # Databricks provisioning capability (3-layer architecture)
│       ├── __init__.py        # Exports all databricks components
│       ├── capability.py      # DatabricksCapability main class
│       ├── README.md          # Capability documentation
│       │
│       ├── core/              # Business Logic Layer
│       │   ├── __init__.py
│       │   ├── config.py      # Configuration (instance types, pricing, regions)
│       │   ├── intent_parser.py   # NL parsing with Azure OpenAI (was: intent_recognizer)
│       │   └── decision_maker.py  # Configuration decisions (was: decision_engine)
│       │
│       ├── models/            # Data Models Layer
│       │   ├── __init__.py
│       │   └── schemas.py     # Pydantic data classes (was: models.py)
│       │
│       └── provisioning/      # Infrastructure Layer
│           └── terraform/
│               ├── __init__.py
│               ├── generator.py   # Terraform code generation
│               └── executor.py    # Terraform execution
│
├── templates/                 # Terraform Jinja2 templates (project root)
│   ├── main.tf.j2
│   ├── variables.tf.j2
│   └── ...
│
└── tests/
    ├── test_orchestrator.py   # Phase 1 + 1.5 tests
    ├── test_capability_integration.py # Phase 2 tests
    ├── test_decision_maker.py # Was: test_decision_engine.py
    ├── test_maf_setup.py      # Phase 0 tests
    └── ...
```

### Key Patterns

#### 1. Data Models
**Convention**: Use Pydantic for all data structures
**Why**: Type validation, schema generation, IDE support

**Example Pattern**:
```python
from pydantic.dataclasses import dataclass

@dataclass
class InfrastructureRequest:
    workspace_name: str
    team: str
    environment: str  # dev, staging, prod
    # ... other fields
```

**Current Implementation**: See `orchestrator/models.py`, `capabilities/databricks/models/schemas.py`

#### 2. LLM Integration
**Convention**: Use agent frameworks (not raw OpenAI SDK)
**Why**:
- Automatic conversation context management
- Built-in function calling support
- Observability and middleware hooks

**Pattern**:
- Agent creation: Define name, instructions (system prompt), available tools
- Message processing: Framework handles history automatically
- Tool integration: Framework invokes functions and manages responses

**Current Implementation**:
- Framework: Microsoft Agent Framework (MAF) 1.0.0b251105
- See `orchestrator/orchestrator_agent.py` for patterns
- Conversation context managed automatically by framework

#### 3. Tool Registration
**Convention**: Use dynamic registration (not hardcoded dispatch)
**Why**: Scales from 3 tools to 300+ without code changes

**Pattern**:
- Tools register themselves via decorators
- Schemas auto-generated from type hints
- Dynamic dispatch by tool name (no if/elif chains)

**Example**:
```python
@tool_manager.register("Tool description")
def my_tool(param: str) -> str:
    """Function automatically registered and available to agent."""
    return json.dumps(result)
```

**Current Implementation**: See `orchestrator/tool_manager.py` for registry pattern

#### 3. Terraform Generation (use Jinja2)
```python
from jinja2 import Template

def generate_main_tf(decision: InfrastructureDecision) -> str:
    template = Template(Path("templates/main.tf.j2").read_text())
    return template.render(
        workspace_name=decision.workspace_name,
        instance_types=decision.instance_types,
        # ... other variables
    )
```

#### 4. Subprocess Management (capture output)
```python
result = subprocess.run(
    ["terraform", "plan"],
    cwd=working_dir,
    capture_output=True,
    text=True,
    timeout=300
)
```

### Testing Conventions
- Unit tests: `tests/test_<module>.py`
- Integration tests: `tests/integration/test_<flow>.py`
- Use pytest fixtures for common setup
- Mock external calls (OpenAI, Terraform)

### Configuration
- Store secrets in `.env` (never commit)
- Use `python-dotenv` to load env vars
- Validate config on startup

### Error Handling
```python
class AgentError(Exception):
    """Base exception for agent errors"""
    pass

class ValidationError(AgentError):
    """Validation failed"""
    pass

class DeploymentError(AgentError):
    """Terraform deployment failed"""
    pass
```

### Logging
```python
import logging

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

# Use throughout code
logger.info("Starting deployment...")
logger.error(f"Deployment failed: {error}")
```

## When Generating Code

### DO:
✅ Add type hints to all function signatures
✅ Include docstrings with examples
✅ Handle errors gracefully
✅ Log important operations
✅ Validate inputs with Pydantic
✅ Use context managers for files
✅ Make code testable (inject dependencies)
✅ Follow the data models in PRD

### DON'T:
❌ Hardcode credentials or secrets
❌ Use `print()` for logging
❌ Ignore error cases
❌ Create deeply nested code
❌ Mix concerns in single function
❌ Use global state
❌ Generate production infrastructure without approval

## Common Tasks

### Understanding the Orchestrator
**Current**: MAF-based conversational orchestrator that:
- Engages in multi-turn conversations
- Uses tools for capability discovery, naming, cost estimation
- Maintains context automatically via MAF
- Prepares infrastructure plans (not yet executing)

### Working with Tools
**Pattern**: Use decorator-based registration
**Adding New Tool**:
1. Define function in `orchestrator/tools.py`
2. Add `@tool_manager.register("Description")` decorator
3. Use modern type hints for auto-schema generation
4. Tool is automatically available to agent

### Working with Capabilities
**Pattern**: Implement BaseCapability interface in `capabilities/<name>/`
**Adding New Capability**:
1. Create `capabilities/<name>/` directory
2. Create `capability.py` implementing `BaseCapability`
3. Register in `orchestrator/orchestrator_agent.py::_register_capabilities()`
4. Add to `orchestrator/capability_registry.py`
5. Create integration tests in `tests/test_<name>_integration.py`

**Capability Structure**:
- `plan()`: Generate deployment plan (dry-run, estimate costs)
- `execute()`: Run actual deployment after approval
- `validate()`: Optional pre-flight checks
- `rollback()`: Optional cleanup on failure

**See**: `capabilities/databricks/` for working example

### Integration Points (Future)
- Multi-capability workflows (Phase 3+)
- Approval gates and state management (Phase 3+)
- Persistent conversation state (Phase 3+)

## Example Workflows

### Current: End-to-End Databricks Provisioning
```
User: "I need Databricks for ML team"
    ↓
Orchestrator: Asks clarifying questions (team name, environment, region)
    ↓
Orchestrator: Uses tools to discover capabilities, suggest names, estimate costs
    ↓
Orchestrator: Proposes infrastructure plan
    ↓
Orchestrator: Calls DatabricksCapability.plan()
    ↓
DatabricksCapability: IntentParser → DecisionMaker → TerraformGenerator
    ↓
Orchestrator: Shows plan, gets approval
    ↓
Orchestrator: Calls DatabricksCapability.execute()
    ↓
DatabricksCapability: TerraformExecutor deploys to Azure
    ↓
Return: Working Databricks workspace with URL
```

**Status**: ✅ Working end-to-end, deployed to production Azure

## Questions to Ask Before Generating

1. What's the exact data type for inputs/outputs?
2. How should errors be handled?
3. What validation is needed?
4. Should this be mocked in tests?
5. Does this need logging?

## Documentation Guidelines

### Creating Status/Summary Documents

**Naming Convention**: When creating documentation about current status, summaries, or snapshots, prefix with date:

```
<YYYY-MM-DD>-<descriptive-name>.md
```

**Examples**:
- `2025-11-10-DATABRICKS_REFACTORING_SUMMARY.md`
- `2025-11-10-SESSION_SUMMARY.md`
- `2025-11-10-REPO_STATUS.md`

**Why**:
- Clear historical tracking
- Easy to identify document age
- Multiple snapshots don't overwrite each other
- Can see evolution over time

**Where to put them**:
- `docs/` - For project-level documentation
- `docs/implementation_status/` - For phase-specific progress

**Don't prefix**:
- Living documents (README.md, CURRENT_STATE.md, ARCHITECTURE_EVOLUTION.md)
- Reference docs (PRD.md, API specs)
- How-to guides (capabilities/README.md)

## References
- PRD: `/docs/PRD.md`
- Data Models: See PRD Section "Data Models"
- API Specs: See PRD Section "API Specifications"
- File Structure: See PRD Section "File Structure"

## Spike Constraints
This is a POC/spike, so:
- Focus on core functionality over polish
- Hardcode reasonable defaults where needed
- Skip advanced error recovery
- Don't build UI (CLI only)
- Don't integrate with Jira/external systems yet

## Guidance Philosophy

**This file balances specificity with flexibility:**
- ✅ **DO specify**: Core principles, patterns, and conventions that should persist
- ✅ **DO specify**: Current tech stack and architecture decisions
- ⚠️ **BE CAREFUL**: Overly specific implementation details that may evolve
- ❌ **AVOID**: Hardcoding exact workflows that user requirements may change

**Why?** This project is a spike/POC exploring the best approach to infrastructure automation. As we learn from each phase, we refactor and improve. The instructions document current state while acknowledging evolution.

**Update frequency**: Review after each completed phase to keep aligned with actual implementation.

## Recent Updates

### November 10, 2025 - Databricks Capability Refactoring
- 🏗️ **Three-layer architecture**: Organized databricks capability into `core/`, `models/`, `provisioning/` layers
- 📦 **File reorganization**: Moved 6 files to layer-based structure
- 🔄 **Class renames**: `IntentRecognizer` → `IntentParser`, `DecisionEngine` → `DecisionMaker`
- 📝 **Documentation**: Added `capabilities/databricks/README.md`, `docs/DATABRICKS_REFACTORING_SUMMARY.md`, `docs/2025-11-10-*.md` files
- ✅ **All 94 tests passing** - Zero functionality lost

**Layer Responsibilities**:
- `core/` - Business logic (config, intent parsing, decision making)
- `models/` - Data structures (Pydantic schemas)
- `provisioning/` - Infrastructure deployment (Terraform generation/execution)

**Template**: This structure serves as template for future capabilities (Azure OpenAI, AKS, etc.)

### November 10, 2025 (Earlier) - Legacy Code Cleanup
- ❌ Removed `agent/infrastructure_agent.py` - Legacy single-shot wrapper (307 lines)
- ❌ Removed `tests/test_infrastructure_agent.py` - Tests for legacy code (434 lines, 19 tests)
- ❌ Removed `agent/` directory - Empty after cleanup
- 📦 Moved `config.py` → `capabilities/databricks/core/config.py` - Part of refactoring
- ✅ Result: 741 lines removed, cleaner codebase

**Impact**: Codebase now has single clear pattern (orchestrator → capability flow) with scalable layered architecture.

## Success Definition
Code is successful when:
1. All tests pass (currently 94/94 ✅)
2. Can deploy a workspace end-to-end (working in production ✅)
3. Takes <20 minutes from request to working workspace (~13 min ✅)
4. Code is readable and maintainable (clean architecture ✅)
5. Follows patterns in this document
