from temporalio import workflow
from pydantic import BaseModel
from datetime import timedelta
from typing import Any, Callable, Coroutine, Literal
from json_logic import jsonLogic, get_var
from filters import Filter
import logging

logging.basicConfig(level=logging.INFO)


class Step(BaseModel):
    id: str | None = None
    type: str
    action: str | None = None
    inputs: dict[str, Any] | None = None
    condition: dict[str, Any] | None = None
    items_path: str | None = None
    filters: list[Filter] | None = None

class FilterStep(Step):
    type: Literal["filter"]
    items_path: str
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


StepHandler = Callable[[Step, dict[str, Any]], Coroutine[Any, Any, dict[str, Any]]]


async def execute_action(step: Step, state: dict[str, Any]) -> dict[str, Any]:
    if step.action is None:
        raise ValueError("Action is required")

    if step.id is None:
        raise ValueError("Action step ID is required")

    result = await workflow.execute_activity(
        step.action,
        args=[step.inputs, step.filters],
        start_to_close_timeout=timedelta(seconds=10),
    )

    return result


async def execute_filter(step: Step, state: dict[str, Any]) -> dict[str, Any]:
    if not step.items_path:
        raise ValueError(f"Filter step '{step.id}' is missing 'items_path'")
    if not step.condition:
        raise ValueError(f"Filter step '{step.id}' is missing 'condition'")

    items = get_var(state["node_outputs"], step.items_path)

    if not isinstance(items, list):
        return {"matched": []}

    matched = [item for item in items if jsonLogic(step.condition, item)]
    return {"matched": matched}

STEP_REGISTRY: dict[str, StepHandler] = {
    "filter": execute_filter,
    "action": execute_action,
}


async def execute_step(step: Step, state: dict[str, Any]) -> dict[str, Any]:
    handler = STEP_REGISTRY.get(step.type)

    if handler is None:
        raise ValueError(f"Unknown step type: {step.type}")

    return await handler(step, state)


@workflow.defn
class DynamicWorkflow:
    @workflow.run
    async def run(self, definition: WorkflowDefinition):
        state: dict[str, Any] = {"node_outputs": {}}

        assert definition.vertices

        next_map = {e.from_: e.to for e in definition.edges}
        start_nodes = set(next_map) - set(next_map.values())

        assert start_nodes, "No start node (cycle?)"

        current_id: str | None = start_nodes.pop()

        while current_id:
            if current_id == "END":
                break

            node = definition.vertices[current_id]
            node.id = current_id
            result = await execute_step(node, state)
            state["node_outputs"][node.id] = result
            workflow.logger.info(f"Node outputs: {state['node_outputs']}")
            current_id = next_map.get(current_id)

        return state