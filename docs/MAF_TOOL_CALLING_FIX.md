# MAF Tool Calling Fix - November 7, 2025

## Problem

The orchestrator was experiencing "Maximum consecutive function call errors reached (3)" when trying to use tools with Microsoft Agent Framework (MAF). The LLM would attempt to call tools but they would fail silently, causing the agent to retry and eventually give up.

## Root Causes

### 1. Passing Schemas Instead of Functions

**Wrong Approach:**
```python
# ❌ Passing wrapped OpenAI function schemas
tool_schemas = tool_manager.get_schemas(wrapped=True)  # Returns [{"type": "function", "function": {...}}]
agent = client.create_agent(
    tools=tool_schemas  # MAF expects functions, not schemas!
)
```

**Correct Approach:**
```python
# ✅ Passing actual Python functions
tool_functions = tool_manager.get_tool_functions()  # Returns [func1, func2, ...]
agent = client.create_agent(
    tools=tool_functions  # MAF auto-generates schemas from functions
)
```

### 2. Complex Dictionary Parameters

MAF had trouble with complex dict parameters like `configuration: dict[str, Any]`.

**Wrong Approach:**
```python
def estimate_cost(
    capability: str,
    configuration: dict[str, Any]  # ❌ Complex dict causes parsing issues
) -> str:
    enable_gpu = configuration.get("enable_gpu", False)
    workload_type = configuration.get("workload_type", "ml")
```

**Correct Approach:**
```python
def estimate_cost(
    capability: Annotated[str, Field(description="Capability name")],
    enable_gpu: Annotated[bool, Field(description="Whether GPU support is needed")],
    workload_type: Annotated[str, Field(description="Workload type")]
) -> str:
    # Parameters passed directly, no dict unpacking needed
```

### 3. Missing Type Annotations

**Wrong Approach:**
```python
def select_capabilities(capabilities: list[str], rationale: str) -> str:
    """Validate and confirm infrastructure capability selection."""
```

**Correct Approach:**
```python
def select_capabilities(
    capabilities: Annotated[list[str], Field(description="List of capability identifiers")],
    rationale: Annotated[str, Field(description="Why these capabilities were selected")]
) -> str:
    """Validate and confirm infrastructure capability selection."""
```

## Solution Implementation

### Changes to `orchestrator/tool_manager.py`

Added method to return actual function objects:

```python
def get_tool_functions(self) -> list[Callable]:
    """
    Get all registered tool functions for MAF agent creation.

    MAF expects actual Python functions (not schemas) and will handle
    schema generation and tool calling automatically.
    """
    return list(self.tools.values())
```

### Changes to `orchestrator/orchestrator_agent.py`

```python
# Before
tool_schemas = tool_manager.get_schemas(wrapped=True)
return client.create_agent(tools=tool_schemas)

# After
tool_functions = tool_manager.get_tool_functions()
return client.create_agent(tools=tool_functions)
```

Simplified tool execution - MAF handles this automatically:

```python
# Before: Manual tool execution loop with error handling
if hasattr(response, "tool_calls") and response.tool_calls:
    for tool_call in response.tool_calls:
        # Execute tools manually...

# After: MAF handles tool calling automatically
response = await self.agent.run(user_message, thread=self.thread)
return response.text
```

### Changes to `orchestrator/tools.py`

1. Added proper type annotations with `Annotated` and `Field`
2. Broke down complex dict parameters into individual parameters
3. Simplified function signatures

## How MAF Tool Calling Works

According to [MAF documentation](https://learn.microsoft.com/en-us/agent-framework/user-guide/agents/agent-tools):

1. **Agent Creation**: Pass actual Python functions to `create_agent(tools=[...])`
2. **Schema Generation**: MAF auto-generates OpenAI function schemas from:
   - Function name and docstring
   - Type annotations (with `Annotated[T, Field(description="...")]`)
   - Parameter names and defaults
3. **Tool Execution**: MAF handles calling tools automatically during `agent.run()`
4. **Result Handling**: Tool results are automatically fed back to the LLM

## Testing

Created `test_e2e_conversation.py` to validate:
- ✅ Single-turn conversation with all details provided
- ✅ Multi-turn conversation with gradual information gathering
- ✅ All tools called successfully (select_capabilities, suggest_naming, estimate_cost, execute_deployment)
- ✅ Conversation context maintained across turns
- ✅ Thread persistence working correctly

## Key Learnings

1. **Trust the Framework**: MAF is designed to handle tool calling automatically. Don't try to manually implement what the framework provides.

2. **Use Simple Parameters**: Avoid complex nested dicts. Break them into individual parameters for better LLM understanding and tool calling reliability.

3. **Type Annotations Matter**: Use `Annotated[T, Field(description="...")]` for better schema generation and LLM understanding.

4. **Thread Management**: Always pass the thread to `agent.run()` and update it from the response to maintain conversation context.

5. **Let MAF Handle Errors**: Don't wrap tool calling in try/except. Let MAF handle retries and error reporting.

## References

- [MAF Agent Tools](https://learn.microsoft.com/en-us/agent-framework/user-guide/agents/agent-tools?pivots=programming-language-python)
- [MAF Multi-Turn Conversations](https://learn.microsoft.com/en-us/agent-framework/user-guide/agents/multi-turn-conversation?pivots=programming-language-python)
- [MAF Running Agents](https://learn.microsoft.com/en-us/agent-framework/user-guide/agents/running-agents?pivots=programming-language-python)
