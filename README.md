## Dynamic Temporal Workflow Generator 

This is a hands on project to build my own N8N workflow creator style, the idea is to be able to send a JSON file with the structure of the workflow to a Fast API server, and that will create a Temporal Workflow to execute the actual task. Also I want to include two AI Agents: One in-charge of design and review workflows (Calling through HTTp) and other to be able to integrate as an actual Agentic Node (running in the actual engine, not as an REST API).

I'm using a JSON as my DSL to be able to convert this into actions (the unit of Temporal), and with that I have two types on nodes:

- Filter nodes: Performed using JSON Logic 
- ACtion nodes: Perfomed with a simple query builder

## How to run it
There is a Docker compose that turns on all the requiered services 

- Fast API server to trigger the workflows
- Temporal
- Google ADK Fast API server with the agent
- Temporal worker 

You only need to run 

```bash
docker compose up --build
```

The only dependency is having Docker :)

## Technology

- Python 3.12
- UV
- Ruff
- Google ADK 1.33
- Temporal SDK 1.27
- Fast API 0.136.1
- Docker

## How it works?

