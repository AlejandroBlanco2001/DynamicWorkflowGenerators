"""
Module that contains all the tools (database operations) to be used by the actions and
the agent. Mostly to seperate this from the actions, so we can attach tools to the agent without messing with Temporal.
"""

from sqlmodel import select, Session
from server.models import Projects, Clients, engine
from server.schemas import Filter
from typing import Literal, Callable, Any

AVAILABLE_OPERATORS = Literal[
    "eq",
    "neq",
    "gt",
    "gte",
    "lt",
    "lte",
    "contains",
]

operators: dict[AVAILABLE_OPERATORS, Callable] = {
    "eq": lambda field, value: field == value,
    "neq": lambda field, value: field != value,
    "gt": lambda field, value: field > value,
    "gte": lambda field, value: field >= value,
    "lt": lambda field, value: field < value,
    "lte": lambda field, value: field <= value,
    "contains": lambda field, value: value in field,
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

async def _build_statement(statement: Any, filters: list[Filter], entity: str) -> Any:
    for filter in filters:
        if filter.field not in QUERYBALE_FIELDS[entity]:
            raise ValueError(f"Field {filter.field} not found in {entity}")

        if filter.operator not in operators:
            raise ValueError(f"Operator {filter.operator} not found in operators")

        column = QUERYBALE_FIELDS[entity][filter.field]
        operator = operators[filter.operator]
        value = filter.value

        statement = statement.where(operator(column, value))

    return statement

async def get_projects(filters: list[Filter] | None = None) -> list[Projects]:
    projects = []

    with Session(engine) as session:
        statement = select(Projects)

        if filters:
            statement = await _build_statement(statement, filters, "projects")
        else:
            statement = statement.limit(10)

        projects = session.exec(statement).all()

    return [project.model_dump() for project in projects]

async def get_clients(filters: list[Filter] | None = None) -> list[Clients]:
    clients = []

    with Session(engine) as session:

        statement = select(Clients)


        if filters:
            statement = await _build_statement(statement, filters, "clients")
        else:
            statement = statement.limit(10)

        clients = session.exec(statement).all()

    return [client.model_dump() for client in clients]