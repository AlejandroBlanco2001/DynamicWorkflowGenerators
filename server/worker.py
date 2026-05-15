import os
import asyncio
from temporalio.client import Client
from temporalio.worker import Worker
from server.workflow import DynamicWorkflow
from server.actions import get_clients, get_projects

async def main():
    temporal_address = os.getenv("TEMPORAL_ADDRESS", "localhost:7233")
    client = await Client.connect(temporal_address)

    worker = Worker(
        client,
        task_queue="workflow",
        workflows=[DynamicWorkflow],
        activities=[get_clients, get_projects],
    )

    await worker.run()

if __name__ == "__main__":
    asyncio.run(main())