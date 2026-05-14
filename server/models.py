from sqlmodel import Field, SQLModel, Relationship, create_engine, Session
from typing import Annotated
from fastapi import Depends

class Clients(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    name: str = Field(index=True)
    email: str = Field(index=True)
    projects: list["Projects"] = Relationship(back_populates="client")

class Projects(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    name: str = Field(index=True)
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
    client = Clients(name="John Doe", email="john.doe@example.com")
    client2 = Clients(name="Jane Doe", email="test@test.com")
    session.add_all([client, client2])
    session.flush()

    assert client.id is not None

    project = Projects(name="Project 1", client_id=client.id)
    session.add(project)
    session.commit()

SessionDep = Annotated[Session, Depends(get_session)]