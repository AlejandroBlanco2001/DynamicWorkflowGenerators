import httpx
BASE_URL = "http://localhost:8000"

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
