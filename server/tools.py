"""
Module that contains all the tools (database operations) to be used by the actions and
the agent. Mostly to seperate this from the actions, so we can attach tools to the agent without messing with Temporal.
"""

from sqlmodel import SQLModel, select, Session
from server.models import Projects, Clients, engine, Invoices
from typing import Literal, Callable, Any, Optional, get_origin, get_args

import logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def apply_field_mapping(items: list[dict], mapping: dict[str, Any]) -> list[dict]:
    """Apply field mapping to transform items.

    Args:
        items: List of source items to transform
        mapping: Dict where key is output field, value is either:
                 - string: source field name (rename/extract)
                 - any other type: literal value to add to each item

    Returns:
        List of transformed items with fields mapped according to mapping config
    """
    result = []
    for item in items:
        transformed = {}
        for output_field, source_or_value in mapping.items():
            if isinstance(source_or_value, str) and source_or_value in item:
                transformed[output_field] = item[source_or_value]
            else:
                transformed[output_field] = source_or_value
        result.append(transformed)
    return result

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

async def _build_statement(statement: Any, filters: list[dict], entity: str, combine: str = "and") -> Any:
    """Apply filters to a SQLModel statement.

    Args:
        statement: SQLModel select statement to filter
        filters: List of filter dicts with structure: {"field": str, "operator": str, "value": Any}
                 Valid operators: eq, neq, gt, gte, lt, lte, contains
        entity: Entity type ("clients" or "projects") for validating queryable fields
        combine: "and" (default) to combine filters with AND, "or" to combine with OR
    """
    if not filters:
        return statement

    conditions = []

    for filter in filters:
        if filter['field'] not in QUERYBALE_FIELDS[entity]:
            raise ValueError(f"Field {filter['field']} not found in {entity}")

        if filter['operator'] not in operators:
            raise ValueError(f"Operator {filter['operator']} not found in operators")

        column = QUERYBALE_FIELDS[entity][filter['field']]
        operator = operators[filter['operator']]
        value = filter['value']

        conditions.append(operator(column, value))

    if combine == "or":
        from sqlalchemy import or_
        statement = statement.where(or_(*conditions))
    else:
        from sqlalchemy import and_
        statement = statement.where(and_(*conditions))

    return statement

async def get_projects(filters: Optional[list[dict]] = None, filter_combine: str = "and") -> list[Projects]:
    """Retrieve projects from database with optional filtering.

    Args:
        filters: Optional list of filter dicts with structure:
                {"field": "name"|"status", "operator": "eq"|"neq"|"gt"|"gte"|"lt"|"lte"|"contains", "value": Any}
        filter_combine: "and" (default) or "or" - how to combine multiple filters

    Returns:
        List of project dicts. Returns up to 10 projects if no filters provided.
    """
    projects = []

    with Session(engine) as session:
        statement = select(Projects)

        if filters:
            statement = await _build_statement(statement, filters, "projects", filter_combine)
        else:
            statement = statement.limit(10)

        logger.info(f"Statement: {statement}")
        projects = session.exec(statement).all()

    return [project.model_dump() for project in projects]

async def get_clients(filters: Optional[list[dict]] = None, filter_combine: str = "and") -> list[Clients]:
    """Retrieve clients from database with optional filtering.

    Args:
        filters: Optional list of filter dicts with structure:
                {"field": "email"|"name", "operator": "eq"|"neq"|"gt"|"gte"|"lt"|"lte"|"contains", "value": Any}
        filter_combine: "and" (default) or "or" - how to combine multiple filters

    Returns:
        List of client dicts. Returns up to 10 clients if no filters provided.
    """
    clients = []

    with Session(engine) as session:
        statement = select(Clients)

        if filters:
            statement = await _build_statement(statement, filters, "clients", filter_combine)
        else:
            statement = statement.limit(10)

        clients = session.exec(statement).all()

    return [client.model_dump() for client in clients]

async def create_invoice(invoices: list[Invoices]) -> list[Invoices]:
    """Create an invoice for a project.

    Args:
        invoice: Pydantic model of the invoice to create

    Returns:
        Invoice object.
    """
    with Session(engine) as session:
        session.add_all(invoices)
        session.commit()

    return [invoice for invoice in invoices]


def _type_to_string(tp):
    """Convert Python/typing types into readable strings."""
    origin = get_origin(tp)

    if origin is None:
        return getattr(tp, "__name__", str(tp))

    if origin is list:
        args = get_args(tp)
        return f"list[{_type_to_string(args[0])}]"

    if origin is dict:
        k, v = get_args(tp)
        return f"dict[{_type_to_string(k)}, {_type_to_string(v)}]"

    if origin is tuple:
        args = get_args(tp)
        return f"tuple[{', '.join(_type_to_string(a) for a in args)}]"

    return str(tp)

async def _get_sqlmodel_schema(model: type[SQLModel]):
    """Extract schema from SQLModel for prompt generation."""
    fields = {}

    model_fields = getattr(model, "model_fields", {})

    for field_name, field_info in model_fields.items():
        annotation = field_info.annotation

        fields[field_name] = {
            "type": _type_to_string(annotation),
            "required": field_info.is_required(),
            "default": (
                None
                if field_info.default is ...
                else field_info.default
            ),
            "description": field_info.description,
        }

    return {
        "model": model.__name__,
        "fields": fields,
    }

async def model_to_prompt(model: type[SQLModel]) -> str:
    """Generate prompt text describing a SQLModel's schema for agent instruction."""
    schema = await _get_sqlmodel_schema(model)

    lines = [f"Model: {schema['model']}"]

    for name, metadata in schema['fields'].items():
        required = "required" if metadata['required'] else "optional"

        lines.append(
            f"  - {name}: {metadata['type']} {required}"
        )

    return "\n".join(lines)