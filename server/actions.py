from temporalio import activity
from sqlmodel import select, Session
from typing import Any, Literal, Callable
from server.models import Clients, Projects, engine
from server.schemas import Filter
import logging

logging.basicConfig(level=logging.INFO)
LOG = logging.getLogger(__name__)

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

async def build_statement(statement: Any, filters: list[Filter], entity: str) -> Any:
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

@activity.defn(name="get_clients")
async def get_clients(input: dict[str, Any], filters: list[Filter] | None = None) -> dict[str, list[Any]]:
    with Session(engine) as session:
        statement = select(Clients)

        LOG.info(f"Building statement for clients with filters: {filters}")

        if filters:
            statement = await build_statement(statement, filters, "clients")
        else:
            statement = statement.limit(10)

        clients = session.exec(statement).all()

        return {
            "items": [
                client.model_dump()
                for client in clients
            ]
        }


@activity.defn(name="get_projects")
async def get_projects(input: dict[str, Any], filters: list[Filter] | None = None) -> dict[str, list[Any]]:

    with Session(engine) as session:

        statement = select(Projects)

        if filters:
            statement = await build_statement(statement, filters, "projects")
        else:
            statement = statement.limit(10)

        projects = session.exec(statement).all()

        return {
            "items": [
                project.model_dump()
                for project in projects
            ]
        }


REGISTRY = {
    "get_clients": get_clients,
    "get_projects": get_projects,
}

ACTION_METADATA = {
    "get_clients": {
        "description": "Fetch clients from the database",
        "filterable_fields": list(QUERYBALE_FIELDS["clients"].keys()),
        "output": {"items": "list of client objects"},
    },
    "get_projects": {
        "description": "Fetch projects from the database",
        "filterable_fields": list(QUERYBALE_FIELDS["projects"].keys()),
        "output": {"items": "list of project objects"},
    },
}