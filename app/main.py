import os
import uvicorn
from fastapi import FastAPI, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from app.models import Base
from app import models
from app.database import engine
from app.routes import auth, roles, users, categories, questions, test, candidates

models.Base.metadata.create_all(bind=engine)

app = FastAPI(title="Interview Test Platform")

ALLOWED_ORIGINS = [
    "http://localhost:3000",  # Local development
    "https://interview-test-platform-front-end.vercel.app",
]
app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,  # Specific origins only
    allow_credentials=True,  # Required for cookies/auth
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS", "PATCH"],
    allow_headers=["*"],
    expose_headers=["*"],
    max_age=3600,  # Cache preflight requests for 1 hour
)

@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    # Handle Pydantic validation errors - Custom
    errors = exc.errors()

    # Check if it's a JSON decode error (malformed JSON like {"password":})
    if errors and errors[0].get("type") == "json_invalid":
        return JSONResponse(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            content={
                "status": 422,
                "error": "Invalid JSON format. Please check your request body."
            }
        )

    # Handle missing required fields
    if errors and errors[0].get("type") == "missing":
        missing_field = errors[0].get("loc")[-1]  # Get field name
        return JSONResponse(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            content={
                "status": 422,
                "error": f"{missing_field} is a required field"
            }
        )

    # Handle empty strings or validation failures
    if errors and errors[0].get("type") in ["string_too_short", "value_error"]:
        field_name = errors[0].get("loc")[-1]
        return JSONResponse(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            content={
                "status": 422,
                "error": f"{field_name} cannot be empty"
            }
        )

    # Generic validation error (type mismatches, etc.)
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "status": 422,
            "error": "Validation error",
            "details": errors
        }
    )


app.include_router(auth.router)
app.include_router(roles.router)
app.include_router(users.router)
app.include_router(categories.router)
app.include_router(questions.router)
app.include_router(test.router)
app.include_router(candidates.router)

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

if __name__ == "__main__":
    port = int(os.getenv("PORT", 10000))  # defaults to 10000
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=port,
        proxy_headers=True,
        forwarded_allow_ips="*"
    )
    
if __name__ == "__main__":

    port = int(os.environ.get("PORT", 8000))
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=port
    )