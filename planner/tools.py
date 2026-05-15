import httpx
from google.adk.tools.tool_context import ToolContext

BASE_URL = "http://127.0.0.1:3000"

COMPLETE_REVIEW_RESULT = "PASSED"

async def get_actions_operators():
    """
    Get all the actions and operators available to create a workflow.
    """
    try:
        async with httpx.AsyncClient(base_url=BASE_URL) as client:
            response = await client.get("/actions")
            return response.json()
    except Exception as e:
        return {"error": f"Error getting actions and operators: {e}"}


async def exit_evaluation_loop(tool_context: ToolContext):
    """
    Exit the evaluation loop and return the proposed workflow.
    """
    print("Exiting evaluation loop and returning the proposed workflow.")
    tool_context.actions.escalate = True
    tool_context.actions.skip_summarization = True
    return {}