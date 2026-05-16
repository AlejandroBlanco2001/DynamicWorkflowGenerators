from pydantic import BaseModel
from typing import Any, Literal
from dataclasses import dataclass

@dataclass
class Filter:
    field: str
    operator: Literal["eq", "neq", "gt", "gte", "lt", "lte", "contains"]
    value: Any


class Step(BaseModel):
    id: str | None = None
    type: str
    action: str | None = None
    depends_on: list[str] | None = None
    inputs: dict[str, Any] | None = None
    condition: dict[str, Any] | None = None
    items_path: str | None = None
    filters: list[Filter] | None = None

class FilterStep(Step):
    type: Literal["filter"]
    items_path: str | None = None
    condition: dict[str, Any]


class Edge(BaseModel):
    from_: str
    to: str


class WorkflowDefinition(BaseModel):
    version: str
    metadata: dict
    variables: dict
    vertices: dict[str, Step]
    edges: list[Edge]
    timeouts: dict
    permissions: dict

ExecutionState = Literal["pending", "running", "skipped", "completed", "failed"]

class State(BaseModel):
    node_outputs: dict[str, dict[str, Any]]
    execution_state: dict[str, ExecutionState]

class StepsExecuted(BaseModel):
    step_id: str
    step_name: str
    step_type: str
    inputs: str

class ExecutionResult(BaseModel):
    result: Literal["PASSED", "FAILED", "ABORTED"]
    message: str
    items: list[Any]
    steps: list[StepsExecuted]