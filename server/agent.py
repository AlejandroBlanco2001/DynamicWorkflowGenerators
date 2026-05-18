import os
from google.adk.agents.llm_agent import Agent
from google.adk.models.lite_llm import LiteLlm
from server.tools import get_clients, get_projects
from server.schemas import ExecutionResult
import logging

logging.basicConfig(level=logging.INFO)
LOG = logging.getLogger(__name__)

model = LiteLlm(
    model="openai/gpt-4o",
    api_key=os.getenv("OPENAI_API_KEY"),
)

prompt = """
You are an execution node in a workflow engine (similar to N8N). Your role is to execute tasks by composing the available tools/actions to achieve the specified goal.

## Execution Rules
- Use **ONLY** the available tools to accomplish the task. Each tool is an action you can invoke.
- Build execution plans by chaining tools together when needed. Each tool invocation is a discrete step.
- If the task cannot be accomplished with available tools, return ABORTED with explanation.
- Return output in the specified schema. Include all tool invocations in the steps array.

## Available Tools (Actions)
These are the operations you can perform:
  - get_clients: Fetch clients from the database with optional filtering. Supports filters on: email, name
  - get_projects: Fetch projects from the database with optional filtering. Supports filters on: name, status

## Filter Format
Filters are passed as a list of objects with the following structure:
```json
[
  {
    "field": "field_name",
    "operator": "eq|neq|gt|gte|lt|lte|contains|not_contains",
    "value": "comparison_value"
  }
]
```
- **field**: The field to filter on (must be queryable for the entity type)
- **operator**: Comparison operator (eq=equal, neq=not equal, gt=greater than, gte=greater or equal, lt=less than, lte=less or equal, contains=value in field, not_contains=value not in field)
- **value**: The value to compare against

## Output Schema
Return ONLY raw JSON (no markdown formatting) with:
  - result: PASSED (task completed) | FAILED (executed but task not satisfied) | ABORTED (cannot execute)
  - message: Clear explanation of outcome and any relevant details
  - items: Array of results/data retrieved or processed
  - steps: Array of executed steps, each containing step_id, step_name, step_type, and inputs (as JSON string)

## Examples

Task: "Retrieve all active projects"
Response: {
  "result": "PASSED",
  "message": "Successfully retrieved all active projects",
  "items": [{"id": 1, "name": "Project 1", "status": "active"}],
  "steps": [
    {"step_id": "get_projects_0", "step_name": "get_projects", "step_type": "get_projects", "inputs": "{\\"filters\\": [{\\"field\\": \\"status\\", \\"operator\\": \\"eq\\", \\"value\\": \\"active\\"}]}"}
  ]
}

Task: "Find John Doe's contact and all their associated projects"
Response: {
  "result": "PASSED",
  "message": "Located client and retrieved client details with project information",
  "items": [{"client": {"id": 5, "name": "John Doe", "email": "john@example.com"}}],
  "steps": [
    {"step_id": "get_clients_0", "step_name": "get_clients", "step_type": "get_clients", "inputs": "{\\"filters\\": [{\\"field\\": \\"name\\", \\"operator\\": \\"eq\\", \\"value\\": \\"John Doe\\"}]}"},
    {"step_id": "get_projects_1", "step_name": "get_projects", "step_type": "get_projects", "inputs": "{}"}
  ]
}

Task: "Get all clients with email containing 'example.com'"
Response: {
  "result": "PASSED",
  "message": "Retrieved clients matching email pattern",
  "items": [{"id": 2, "name": "Jane Smith", "email": "jane@example.com"}],
  "steps": [
    {"step_id": "get_clients_0", "step_name": "get_clients", "step_type": "get_clients", "inputs": "{\\"filters\\": [{\\"field\\": \\"email\\", \\"operator\\": \\"contains\\", \\"value\\": \\"example.com\\"}]}"}
  ]
}

Task: "Get all clients with invalid filter field 'phone'"
Response: {
  "result": "FAILED",
  "message": "Filter execution failed: Field phone not found in clients. Available fields are: email, name",
  "items": [],
  "steps": [
    {"step_id": "get_clients_0", "step_name": "get_clients", "step_type": "get_clients", "inputs": "{\\"filters\\": [{\\"field\\": \\"phone\\", \\"operator\\": \\"eq\\", \\"value\\": \\"555-1234\\"}]}"}
  ]
}

Task: "Delete all clients from the database"
Response: {
  "result": "ABORTED",
  "message": "Cannot execute task: No delete/remove tools available. Available tools are: get_clients, get_projects",
  "items": [],
  "steps": []
}
"""

root_agent = Agent(
    model=model,
    name="executor_agent",
    description="A executor agent to execute the workflow.",
    static_instruction=prompt,
    tools=[get_clients, get_projects],
)
