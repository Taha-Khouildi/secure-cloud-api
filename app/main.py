from fastapi import FastAPI
from pydantic import BaseModel, Field
from prometheus_fastapi_instrumentator import Instrumentator
from app.database import get_connection
from app.request_size import RequestSizeLimitMiddleware
from fastapi import FastAPI, Request
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.util import get_remote_address

app = FastAPI()
limiter = Limiter(key_func=get_remote_address)

app.state.limiter = limiter
app.add_exception_handler(
    RateLimitExceeded,
    _rate_limit_exceeded_handler,
)

app.add_middleware(RequestSizeLimitMiddleware, max_body_size=1024 * 1024)
Instrumentator().instrument(app).expose(app)

class TodoCreate(BaseModel):
    title: str = Field(min_length=1, max_length=255)


@app.get("/health")
def health():
    return {"status": "ok"}


@app.get("/db-health")
def db_health():
    with get_connection() as conn:
        with conn.cursor() as cursor:
            cursor.execute("SELECT 1")
            result = cursor.fetchone()
            assert result == (1,)

    return {"database": "connected"}


@app.get("/todos")
@limiter.limit("60/minute")
def get_todos(request: Request):
    with get_connection() as conn:
        with conn.cursor() as cursor:
            cursor.execute("SELECT id, title, completed FROM todos ORDER BY id")
            rows = cursor.fetchall()
            return [
                {"id": row[0], "title": row[1], "completed": row[2]}
                for row in rows
            ]


@app.post("/todos", status_code=201)
@limiter.limit("60/minute")
def create_todo(request: Request, todo: TodoCreate):
    with get_connection() as conn:
        with conn.cursor() as cursor:
            cursor.execute(
                "INSERT INTO todos (title) VALUES (%s) RETURNING id, title, completed",
                (todo.title,),
            )
            row = cursor.fetchone()
            return {"id": row[0], "title": row[1], "completed": row[2]}
