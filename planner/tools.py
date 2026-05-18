import os 
import httpx
from google.adk.tools.tool_context import ToolContext
import logging

logging.basicConfig(level=logging.INFO)
LOG = logging.getLogger(__name__)

PORT = os.getenv("API_PORT", 3000)
BASE_URL = f"http://api:{PORT}"

COMPLETE_REVIEW_RESULT = "PASSED"

async def get_actions_operators(tool_context: ToolContext):
    """
    Get all the actions and operators available to create a workflow.
    """
    try:
        async with httpx.AsyncClient(base_url=BASE_URL) as client:
            LOG.info(f"Getting actions and operators from {BASE_URL}")
            response = await client.get("/actions")
            return response.json()
    except Exception as e:
        tool_context.actions.escalate = True
        return {"error": f"Error getting actions and operators: {e}"}


async def exit_evaluation_loop(tool_context: ToolContext):
    """
    Exit the evaluation loop and return the proposed workflow.
    """
    print("Exiting evaluation loop and returning the proposed workflow.")
    tool_context.actions.escalate = True
    tool_context.actions.skip_summarization = True
    return {}