from fastapi import FastAPI
from models import Clients, seed_database, create_db_and_tables, SessionDep
from sqlmodel import select
import uvicorn

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

@app.get('/clients')
def get_clients(session: SessionDep):
    statement = select(Clients)
    result = session.exec(statement)
    return result.all()

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)