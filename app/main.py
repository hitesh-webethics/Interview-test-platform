from fastapi import FastAPI
from pydantic import BaseModel
from app.models import Base
from app import models
from app.database import engine
from app.routes import auth, roles, users, categories, subcategories, questions, test 

models.Base.metadata.create_all(bind=engine)

app = FastAPI(title="Interview Test Platform")

app.include_router(auth.router)
app.include_router(roles.router)
app.include_router(users.router)
app.include_router(categories.router)
app.include_router(subcategories.router)
app.include_router(questions.router)
app.include_router(test.router)

@app.get("/")
def read_root():
    return {"status" : "ok", "message" : "Interview Test Platform - dev server" }

class HelloIn(BaseModel):
    name: str

class HelloOut(BaseModel):
    greeting: str

@app.post("/hello", response_model= HelloOut)
def say_hello(payload: HelloIn):
    return {"greeting": f"Hello, {payload.name}! This endpoint works."}

from app.database import engine
@app.get("/test-db")
def test_db_connnection():
    try:
        with engine.connect () as conn:
            return {"status": "sucess", "message": "Database connection Ok"}
        
    except Exception as e:
        return {"status": "error", "message": str(e)}
    
