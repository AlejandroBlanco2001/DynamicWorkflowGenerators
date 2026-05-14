from sqlmodel import Field, SQLModel, Relationship, create_engine, Session
from typing import Annotated
from fastapi import Depends
from enum import Enum
from mimesis import Person


class ProjectStatus(str, Enum):
    NEGOTIATION = "negotiation"
    PLANNING = "planning"
    DEVELOPMENT = "development"
    FINISHED = "finished"
    REJECTED = "rejected"


class Clients(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    name: str = Field(index=True)
    email: str = Field(index=True)
    projects: list["Projects"] = Relationship(back_populates="client")


class Projects(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    name: str = Field(index=True)
    status: ProjectStatus = Field(default=ProjectStatus.NEGOTIATION)
    client_id: int = Field(foreign_key="clients.id")
    client: Clients = Relationship(back_populates="projects")


sqlite_file_name = "database.db"
sqlite_url = f"sqlite:///{sqlite_file_name}"

engine = create_engine(sqlite_url)


def get_session():
    with Session(engine) as session:
        yield session


def create_db_and_tables():
    SQLModel.metadata.create_all(engine)


def seed_database(session: Session):
    clients = [Clients(name=Person().name(), email=Person().email()) for _ in range(10)]

    session.add_all(clients)
    session.flush()

    statuses = [
        ProjectStatus.NEGOTIATION,
        ProjectStatus.PLANNING,
        ProjectStatus.DEVELOPMENT,
        ProjectStatus.FINISHED,
        ProjectStatus.REJECTED,
    ]

    projects = [
        Projects(
            name=f"Project {client.id}",
            client_id=client.id if client.id is not None else 1,
            status=statuses[index % len(statuses)],
        )
        for index, client in enumerate(clients)
    ]

    session.add_all(projects)
    session.commit()


SessionDep = Annotated[Session, Depends(get_session)]
