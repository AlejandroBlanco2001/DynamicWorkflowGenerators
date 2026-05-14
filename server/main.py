from fastapi import FastAPI, Depends
from models import get_session, Clients, seed_database
from sqlmodel import Session, select
import uvicorn

app = FastAPI()

@app.get("/ping")
def ping():
    return {"message": "pong"}

@app.post("/populate")
def populate(session: Session = Depends(get_session)):
    seed_database(session)
    return {"message": "Database populated"}

@app.get('/clients')
def get_clients(session: Session = Depends(get_session)):
    statement = select(Clients)
    result = session.exec(statement)
    return result.all()

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)