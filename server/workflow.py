from temporalio import workflow
from pydantic import BaseModel
from datetime import timedelta

class WorkflowDefinition(BaseModel):
    version: str
    metadata: dict
    variables: dict
    steps: list[dict]
    edges: list[dict]
    timeouts: dict
    permissions: dict

@workflow.defn
class DynamicWorkflow:
    @workflow.run
    async def run(self, definition: WorkflowDefinition):
        result = None

        for step in definition.steps:
            activity_name = step.get("name")

            if not activity_name:
                raise ValueError(f"Step {step} has no name")

            inputs = step.get("inputs", {})

            result = await workflow.execute_activity(
                activity_name,
                inputs,
                start_to_close_timeout=timedelta(seconds=10)
            )

        return result

