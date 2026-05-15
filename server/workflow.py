from temporalio import workflow
from datetime import timedelta
from typing import Any, Callable, Coroutine
from server.json_logic import jsonLogic, get_var
import logging
from server.graph import build_adjacency_list, topological_sort
from server.schemas import Step, WorkflowDefinition

logging.basicConfig(level=logging.INFO)

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

        adjacency_map = build_adjacency_list(definition.edges)
        execution_order = topological_sort(adjacency_map)

        workflow.logger.info(f"Execution order: {execution_order}")

        for current_id in execution_order:
            node = definition.vertices[current_id]
            node.id = current_id
            result = await execute_step(node, state)
            state["node_outputs"][node.id] = result
            workflow.logger.info(f"Node outputs: {state['node_outputs']}")

        return state