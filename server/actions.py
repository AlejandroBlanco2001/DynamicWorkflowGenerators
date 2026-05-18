import json
import logging
from typing import Any

from google.adk import Runner
from google.adk.sessions.in_memory_session_service import InMemorySessionService
from google.genai import types
from temporalio import activity
from pydantic import ValidationError

import server.tools as tools
from server.agent import root_agent
from server.schemas import Filter, ExecutionResult, State
from server.models import Invoices

logging.basicConfig(level=logging.INFO)
LOG = logging.getLogger(__name__)


@activity.defn(name="agentic_node")
async def agentic_node(
    input: dict[str, Any], filters: list[Filter] | None = None
) -> dict[str, Any]:
    session_service = InMemorySessionService()

    if input["content"] is None:
        raise ValueError("Content is required!")

    session = await session_service.create_session(
        state={}, app_name="agentic_node", user_id="user_dc"
    )

    runner = Runner(
        app_name="agentic_node", agent=root_agent, session_service=session_service
    )

    message = types.Content(role="user", parts=[types.Part(text=input["content"])])

    events_async = runner.run_async(
        session_id=session.id, user_id=session.user_id, new_message=message
    )

    results = []

    # Collect all results from async stream
    async for event in events_async:
        print(f"Event received: {event}")
        results.append(event)

    if not results:
        raise ValueError("No results received from agent")

    try:
        last_result = results[-1]
        if not last_result.content or not last_result.content.parts:
            raise ValueError("Last result has no content parts")

        text = last_result.content.parts[0].text.strip()
        if not text:
            raise ValueError("Content text is empty")

        # Strip markdown JSON
        if text.startswith("```json"):
            text = text[7:]  # Remove ```json
        if text.startswith("```"):
            text = text[3:]  # Remove ```
        if text.endswith("```"):
            text = text[:-3]  # Remove ```

        text = text.strip()

        message = json.loads(text)
        execution_result = ExecutionResult.model_validate(message)
    except Exception as e:
        LOG.error(f"Error parsing message: {e}, last_result: {last_result}")
        raise e

    if not message:
        raise ValueError("No message received from the agent")

    return {"items": execution_result.model_dump()}


@activity.defn(name="get_clients")
async def get_clients(
    input: dict[str, Any], filters: list[Filter] | None = None
) -> dict[str, list[Any]]:
    LOG.info(f"Building statement for clients with filters: {filters}")

    dics_filters = []
    if filters:
        dics_filters = [filter.model_dump() for filter in filters]

    filter_combine = input.get("filter_combine", "and")

    try:
        clients = await tools.get_clients(dics_filters, filter_combine)
    except Exception as e:
        LOG.error(f"Error getting clients: {e}")
        raise e

    return {"items": clients}


@activity.defn(name="get_projects")
async def get_projects(
    input: dict[str, Any], filters: list[Filter] | None = None
) -> dict[str, list[Any]]:
    dics_filters = []

    if filters:
        dics_filters = [filter.model_dump() for filter in filters]

    filter_combine = input.get("filter_combine", "and")

    try:
        projects = await tools.get_projects(dics_filters, filter_combine)
    except Exception as e:
        LOG.error(f"Error getting projects: {e}")
        raise e

    return {"items": projects}

@activity.defn(name="create_invoices")
async def create_invoices(
    input: dict[str, Any],
    filters: list[Filter] | None = None,
    state: State,
) -> dict[str, Any]:
    raw_invoices = input.get("invoices", None)

    if raw_invoices is None:
        raise ValueError("Invoices are required!")

    invoices = []
    try:
        # Handle field mapping if invoices is a dict with "from" and "map"
        if isinstance(raw_invoices, dict) and "from" in raw_invoices and "map" in raw_invoices:
            # Field mapping not supported here - should be handled by workflow executor
            raise ValueError("Field mapping should be applied by workflow executor before reaching action")

        invoices = [Invoices.model_validate(invoice) for invoice in raw_invoices]
        invoices = await tools.create_invoice(invoices)
    except (ValueError, ValidationError) as e:
        LOG.exception("Error validating invoice")
        raise e
    except Exception as e:
        LOG.exception("Error creating invoice")
        raise e

    return {"items": [invoice.model_dump() for invoice in invoices]}


REGISTRY = {
    "get_clients": get_clients,
    "get_projects": get_projects,
    "agentic_node": agentic_node,
    "create_invoices": create_invoices,
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
    "agentic_node": {
        "description": "Execute a task using an AI agent that composes available tools",
        "filterable_fields": [],
        "output": {"items": "array of execution steps with results"},
    },
    "create_invoices": {
        "description": "Create invoices for projects",
        "input": {"invoices": "list of Pydantic models of the invoices to create"},
        "output": {"items": "list of created invoice objects"},
    },
}
