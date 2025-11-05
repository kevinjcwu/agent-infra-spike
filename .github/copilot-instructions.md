# GitHub Copilot Instructions for agent-infra-spike

## Project Overview
This is a spike/POC to build an AI agent that automates Databricks workspace provisioning using LLMs and Terraform. The agent takes natural language requests and deploys production-grade infrastructure in Azure.

## Context Documents
**Primary Reference**: Read `/docs/PRD.md` for complete requirements, architecture, and technical specifications.

## Code Generation Guidelines

### Language & Style
- **Language**: Python 3.10+
- **Style**: Follow PEP 8, use type hints
- **Docstrings**: Google style
- **Error Handling**: Use custom exceptions, log errors
- **Testing**: Write pytest tests for all functions

### Architecture Principles
1. **Separation of Concerns**: Each module has single responsibility
   - `intent_recognizer.py`: LLM integration only
   - `decision_engine.py`: Business logic only
   - `terraform_generator.py`: Template rendering only
   - `terraform_executor.py`: Subprocess management only

2. **Data Flow**: InfrastructureRequest → InfrastructureDecision → TerraformFiles → DeploymentResult

3. **Dependencies**: 
   - OpenAI for LLM (GPT-4)
   - Jinja2 for templating
   - Subprocess for Terraform
   - Pydantic for validation

### File Organization
```
agent/
├── __init__.py
├── infrastructure_agent.py    # Main orchestrator
├── intent_recognizer.py       # LLM parsing
├── decision_engine.py         # Configuration logic
├── terraform_generator.py     # HCL generation
├── terraform_executor.py      # Terraform execution
├── models.py                  # Data classes
└── config.py                  # Configuration
```

### Key Patterns

#### 1. Data Models (use Pydantic dataclasses)
```python
from pydantic.dataclasses import dataclass
from typing import Optional, List

@dataclass
class InfrastructureRequest:
    workspace_name: str
    team: str
    environment: str  # dev, staging, prod
    region: str
    enable_gpu: bool = False
    workload_type: str = "data_engineering"
    cost_limit: Optional[float] = None
```

#### 2. LLM Integration (use OpenAI function calling)
```python
def recognize_intent(user_message: str) -> InfrastructureRequest:
    response = client.chat.completions.create(
        model="gpt-4",
        messages=[{"role": "user", "content": user_message}],
        functions=[infrastructure_request_schema],
        function_call={"name": "create_infrastructure_request"}
    )
    # Parse and return InfrastructureRequest
```

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

### Task 1: Implement Intent Recognizer
**Input**: "Create prod workspace for ML team in East US"
**Output**: InfrastructureRequest with parsed parameters
**Key Logic**: Use OpenAI function calling for structured output

### Task 2: Implement Decision Engine
**Input**: InfrastructureRequest
**Output**: InfrastructureDecision with instance types, costs
**Key Logic**: 
- ML team → GPU instances
- Prod → Premium SKU, larger instances
- Calculate cost estimates

### Task 3: Implement Terraform Generator
**Input**: InfrastructureDecision
**Output**: Dict[filename, content] of Terraform files
**Key Logic**: Use Jinja2 templates in /templates/

### Task 4: Implement Terraform Executor
**Input**: Working directory with Terraform files
**Output**: DeploymentResult with workspace URL
**Key Logic**: 
- Run init, plan, apply
- Parse outputs
- Handle errors

## Example Workflows

### Simple Request Flow
```
User: "Create workspace for data science team"
    ↓
IntentRecognizer: Parse to InfrastructureRequest
    ↓
DecisionEngine: Choose config (Standard_DS3_v2, no GPU)
    ↓
TerraformGenerator: Generate HCL files
    ↓
TerraformExecutor: Deploy to Azure
    ↓
Return: DeploymentResult with URL
```

### With Approval Flow
```
[Same as above until TerraformGenerator]
    ↓
Show plan to user
    ↓
Wait for "yes" confirmation
    ↓
TerraformExecutor: Deploy
```

## Questions to Ask Before Generating

1. What's the exact data type for inputs/outputs?
2. How should errors be handled?
3. What validation is needed?
4. Should this be mocked in tests?
5. Does this need logging?

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

## Success Definition
Code is successful when:
1. All tests pass
2. Can deploy a workspace end-to-end
3. Takes <20 minutes from request to working workspace
4. Code is readable and maintainable
5. Follows patterns in this document