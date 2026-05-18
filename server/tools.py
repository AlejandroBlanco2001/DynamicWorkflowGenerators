"""
Module that contains all the tools (database operations) to be used by the actions and
the agent. Mostly to seperate this from the actions, so we can attach tools to the agent without messing with Temporal.
"""

from sqlmodel import select, Session
from server.models import Projects, Clients, engine
from typing import Literal, Callable, Any, Optional

AVAILABLE_OPERATORS = Literal[
    "eq",
    "neq",
    "gt",
    "gte",
    "lt",
    "lte",
    "contains",
    "not_contains",
]

operators: dict[AVAILABLE_OPERATORS, Callable] = {
    "eq": lambda field, value: field == value,
    "neq": lambda field, value: field != value,
    "gt": lambda field, value: field > value,
    "gte": lambda field, value: field >= value,
    "lt": lambda field, value: field < value,
    "lte": lambda field, value: field <= value,
    "contains": lambda field, value: field.contains(value),
    "not_contains": lambda field, value: ~field.contains(value),
}

QUERYBALE_FIELDS = {
    "clients": {
        "email": Clients.email,
        "name": Clients.name,
    },
    "projects": {
        "name": Projects.name,
        "status": Projects.status,
    },
}

async def _build_statement(statement: Any, filters: list[dict], entity: str) -> Any:
    """Apply filters to a SQLModel statement.

    Args:
        statement: SQLModel select statement to filter
        filters: List of filter dicts with structure: {"field": str, "operator": str, "value": Any}
                 Valid operators: eq, neq, gt, gte, lt, lte, contains
        entity: Entity type ("clients" or "projects") for validating queryable fields
    """
    for filter in filters:
        if filter['field'] not in QUERYBALE_FIELDS[entity]:
            raise ValueError(f"Field {filter['field']} not found in {entity}")

        if filter['operator'] not in operators:
            raise ValueError(f"Operator {filter['operator']} not found in operators")

        column = QUERYBALE_FIELDS[entity][filter['field']]
        operator = operators[filter['operator']]
        value = filter['value']

        statement = statement.where(operator(column, value))

    return statement

async def get_projects(filters: Optional[list[dict]] = None) -> list[Projects]:
    """Retrieve projects from database with optional filtering.

    Args:
        filters: Optional list of filter dicts with structure:
                {"field": "name"|"status", "operator": "eq"|"neq"|"gt"|"gte"|"lt"|"lte"|"contains", "value": Any}

    Returns:
        List of project dicts. Returns up to 10 projects if no filters provided.
    """
    projects = []

    with Session(engine) as session:
        statement = select(Projects)

        if filters:
            statement = await _build_statement(statement, filters, "projects")
        else:
            statement = statement.limit(10)

        projects = session.exec(statement).all()

    return [project.model_dump() for project in projects]

async def get_clients(filters: Optional[list[dict]] = None) -> list[Clients]:
    """Retrieve clients from database with optional filtering.

    Args:
        filters: Optional list of filter dicts with structure:
                {"field": "email"|"name", "operator": "eq"|"neq"|"gt"|"gte"|"lt"|"lte"|"contains", "value": Any}

    Returns:
        List of client dicts. Returns up to 10 clients if no filters provided.
    """
    clients = []

    with Session(engine) as session:
        statement = select(Clients)

        if filters:
            statement = await _build_statement(statement, filters, "clients")
        else:
            statement = statement.limit(10)

        clients = session.exec(statement).all()

    return [client.model_dump() for client in clients]
