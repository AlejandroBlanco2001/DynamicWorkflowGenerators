"""
This module contains the nodes for the workflow, in 
Temporal terms, we can say that this are the Actions"
"""

from temporalio import activity
from models import Clients
from sqlmodel import select
from pydantic import BaseModel
from typing import Any
from sqlmodel import Session
from models import engine

class GenericOutput(BaseModel):
    data: dict[str, Any]

@activity.defn(name="get_clients")
async def get_clients(input: dict[str, Any]) -> GenericOutput:
    with Session(engine) as session:
        statement = select(Clients).limit(10)
        result = session.exec(statement)
        clients = result.all()
        return GenericOutput(data={"clients": clients})
        
REGISTRY = {
    "get_clients": get_clients
}
