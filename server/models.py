from sqlmodel import Field, SQLModel, Relationship, create_engine, Session

class Clients(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    name: str = Field(index=True)
    email: str = Field(index=True)

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

def seed_database(session: Session):
    client = Clients(name="John Doe", email="john.doe@example.com")
    session.add(client)
    session.flush()

    assert client.id is not None

    project = Projects(name="Project 1", client_id=client.id)
    session.add(project)
    session.commit()
