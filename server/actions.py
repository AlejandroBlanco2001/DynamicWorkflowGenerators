from temporalio import activity
from sqlmodel import select, Session
from typing import Any

from models import Clients, Projects, engine

@activity.defn(name="get_clients")
async def get_clients(input: dict[str, Any]) -> dict[str, list[Any]]:

    with Session(engine) as session:

        statement = select(Clients).limit(10)

        clients = session.exec(statement).all()

        return {
            "items": [
                client.model_dump()
                for client in clients
            ]
        }


@activity.defn(name="get_projects")
async def get_projects(input: dict[str, Any]) -> dict[str, list[Any]]:

    with Session(engine) as session:

        statement = select(Projects).limit(10)

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