from fastapi import FastAPI, Depends
from models import Clients, Projects, seed_database, create_db_and_tables, SessionDep
from sqlmodel import select
import uvicorn
from workflow import WorkflowDefinition, DynamicWorkflow
from temporalio.client import Client
import logging

log = logging.getLogger(__name__)


async def get_client():
    client = await Client.connect("localhost:7233")
    yield client


async def lifespan(app: FastAPI):
    create_db_and_tables()
    yield


app = FastAPI(lifespan=lifespan)


@app.get("/ping")
def ping():
    return {"message": "pong"}


@app.post("/populate")
def populate(session: SessionDep):
    seed_database(session)
    return {"message": "Database populated"}


@app.get("/clients")
def get_clients(session: SessionDep):
    statement = select(Clients)
    result = session.exec(statement)
    return result.all()

@app.get("/projects")
def get_projects(session: SessionDep):
    statement = select(Projects)
    result = session.exec(statement)
    return result.all()

@app.post("/workflow")
async def run_workflow(
    definition: WorkflowDefinition,
    client: Client = Depends(get_client),
):
    handler = await client.start_workflow(
        DynamicWorkflow.run,
        definition,
        id="workflow-1",
        task_queue="workflow",
    )

    return {"message": "Workflow started", "workflow_id": handler.id}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)