import asyncio
from temporalio.client import Client
from temporalio.worker import Worker
from workflow import DynamicWorkflow
from actions import get_clients, get_projects

async def main():
    client = await Client.connect("localhost:7233")

    worker = Worker(
        client,
        task_queue="workflow",
        workflows=[DynamicWorkflow],
        activities=[get_clients, get_projects],
    )

    await worker.run()

if __name__ == "__main__":
    asyncio.run(main())