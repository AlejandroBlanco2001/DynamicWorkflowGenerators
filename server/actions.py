from temporalio import activity
from typing import Any
from server.schemas import Filter
import logging
from server.agent import root_agent
from google.adk.sessions.in_memory_session_service import InMemorySessionService
from google.adk import Runner
import server.tools as tools

logging.basicConfig(level=logging.INFO)
LOG = logging.getLogger(__name__)

@activity.defn(name="agentic_node")
async def agentic_node(input: dict[str, Any]) -> dict[str, Any]:
    session_service = InMemorySessionService()

    if input["content"] is None:
        raise ValueError("Content is required!")
    
    session = await session_service.create_session(
      state={}, app_name='agentic_node', user_id='user_dc'
    )

    runner = Runner(
        app_name="agentic_node",
        agent=root_agent,
        session_service=session_service
    )
    
    events_async =  runner.run_async(
        session_id=session.id, user_id=session.user_id, new_message=input["content"]
    )

    async for event in events_async:
        print(f"Event received: {event}")

    return {
        "items": []
    }

@activity.defn(name="get_clients")
async def get_clients(input: dict[str, Any], filters: list[Filter] | None = None) -> dict[str, list[Any]]:
    LOG.info(f"Building statement for clients with filters: {filters}")

    try: 
        clients = await tools.get_clients(filters)
    except Exception as e:
        LOG.error(f"Error getting clients: {e}")
        raise e

    return {
        "items": clients
    }


@activity.defn(name="get_projects")
async def get_projects(input: dict[str, Any], filters: list[Filter] | None = None) -> dict[str, list[Any]]:
    try:
        projects = await tools.get_projects(filters)
    except Exception as e:
        LOG.error(f"Error getting projects: {e}")
        raise e

    return {
        "items": projects
    }


REGISTRY = {
    "get_clients": get_clients,
    "get_projects": get_projects,
}

ACTION_METADATA = {
    "get_clients": {
        "description": "Fetch clients from the database",
        "filterable_fields": list(tools.QUERYBALE_FIELDS["clients"].keys()),
        "output": {"items": "list of client objects"},
    },
    "get_projects": {
        "description": "Fetch projects from the database",
        "filterable_fields": list(tools.QUERYBALE_FIELDS["projects"].keys()),
        "output": {"items": "list of project objects"},
    },
}