from fastapi import FastAPI
from pydantic import BaseModel, Field

from app.database import get_connection

app = FastAPI()


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
def get_todos():
    with get_connection() as conn:
        with conn.cursor() as cursor:
            cursor.execute("SELECT id, title, completed FROM todos ORDER BY id")
            rows = cursor.fetchall()
            return [
                {"id": row[0], "title": row[1], "completed": row[2]}
                for row in rows
            ]


@app.post("/todos", status_code=201)
def create_todo(todo: TodoCreate):
    with get_connection() as conn:
        with conn.cursor() as cursor:
            cursor.execute(
                "INSERT INTO todos (title) VALUES (%s) RETURNING id, title, completed",
                (todo.title,),
            )
            row = cursor.fetchone()
            return {"id": row[0], "title": row[1], "completed": row[2]}
