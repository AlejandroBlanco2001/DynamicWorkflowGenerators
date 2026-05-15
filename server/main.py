import os
from fastapi import FastAPI, Depends
from server.models import Clients, Projects, seed_database, create_db_and_tables, SessionDep
from sqlmodel import select
import uvicorn
from server.workflow import DynamicWorkflow
from server.actions import ACTION_METADATA
from temporalio.client import Client
import logging
from server.schemas import WorkflowDefinition

log = logging.getLogger(__name__)


async def get_client():
    temporal_address = os.getenv("TEMPORAL_ADDRESS", "localhost:7233")
    client = await Client.connect(temporal_address)
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

@app.get("/actions")
def list_actions():
    # TODO: Make the operators a list, so we can just return it without hardcoding the operators
    return {
        "actions": [{"name": name, **meta} for name, meta in ACTION_METADATA.items()],
        "operators": ["eq", "neq", "gt", "gte", "lt", "lte", "contains"],
    }

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
    port = os.getenv("API_PORT", 3000)
    port = int(port)
    uvicorn.run(app, host="0.0.0.0", port=port)