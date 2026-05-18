from temporalio import workflow
from datetime import timedelta
from typing import Any, Callable, Coroutine
from server.json_logic import jsonLogic
import logging
from server.graph import build_adjacency_list, topological_sort
from server.schemas import Step, WorkflowDefinition, State
from server.tools import apply_field_mapping

logging.basicConfig(level=logging.INFO)

StepHandler = Callable[[Step, State], Coroutine[Any, Any, dict[str, Any]]]


async def execute_action(step: Step, state: State) -> dict[str, Any]:
    if step.action is None:
        raise ValueError("Action is required")

    if step.id is None:
        raise ValueError("Action step ID is required")

    # Process field mapping in inputs
    inputs = step.inputs or {}
    if isinstance(inputs, dict):
        processed_inputs = {}
        for key, value in inputs.items():
            if isinstance(value, dict) and "from" in value and "map" in value:
                # Resolve "from" reference to get source items
                from_ref = value["from"]  # e.g., "step_2.items"
                map_config = value["map"]

                if from_ref not in state.node_outputs:
                    raise ValueError(f"Reference '{from_ref}' not found in outputs")

                source_items = state.node_outputs[from_ref].get("items", [])
                if not isinstance(source_items, list):
                    raise ValueError(f"'{from_ref}' is not an array")

                # Apply field mapping
                transformed = apply_field_mapping(source_items, map_config)
                processed_inputs[key] = transformed
            else:
                processed_inputs[key] = value
        inputs = processed_inputs

    timeout = timedelta(seconds=60) if step.action == "agentic_node" else timedelta(seconds=10)

    result = await workflow.execute_activity(
        step.action,
        args=[inputs, step.filters, state],
        start_to_close_timeout=timeout,
    )

    return result


async def execute_filter(step: Step, state: State) -> dict[str, Any]:
    if not step.condition:
        raise ValueError(f"Filter step '{step.id}' is missing 'condition'")

    return {"items": jsonLogic(step.condition, state.node_outputs)}

STEP_REGISTRY: dict[str, StepHandler] = {
    "filter": execute_filter,
    "action": execute_action,
}


async def execute_step(step: Step, state: State) -> dict[str, Any]:
    handler = STEP_REGISTRY.get(step.type)

    assert step.id is not None

    if step.depends_on:
        has_dependencies = all(
            state.node_outputs[dep].get("items")
            for dep in step.depends_on
        )

        if not has_dependencies:
            workflow.logger.info(
                "Step %s depends on %s, skipping execution",
                step.id,
                step.depends_on,
            )

            state.execution_state[step.id] = "skipped"

            return {"items": []}

    if handler is None:
        raise ValueError(f"Unknown step type: {step.type}")

    try:
        result = await handler(step, state)
    except Exception as e:
        workflow.logger.error(f"Error executing step {step.id}: {e}")
        state.execution_state[step.id] = "failed"
        return {"error": str(e)}
    
    state.execution_state[step.id] = "completed"
    return result


@workflow.defn
class DynamicWorkflow:
    @workflow.run
    async def run(self, definition: WorkflowDefinition):
        state: State = State(node_outputs={}, execution_state={})

        assert definition.vertices

        adjacency_map = build_adjacency_list(definition.edges)

        workflow.logger.info(f"Adjacency map: {adjacency_map}")

        execution_order = topological_sort(adjacency_map)

        workflow.logger.info(f"Execution order: {execution_order}")

        for current_id in execution_order:
            # TODO: Think a way to have a single node without the need to have a END node
            if current_id == "END":
                continue
            
            node = definition.vertices[current_id]
            node.id = current_id
            workflow.logger.info(f"Node: {node.inputs}")
            result = await execute_step(node, state)
            state.node_outputs[node.id] = result
            workflow.logger.info(f"Node outputs: {state.node_outputs}")

        return state