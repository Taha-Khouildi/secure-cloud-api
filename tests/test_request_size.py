
from fastapi.testclient import TestClient

from app.main import app


client = TestClient(app)


def test_normal_request_size():
    response = client.get("/health")

    assert response.status_code == 200


def test_malformed_json():
    response = client.post(
        "/todos",
        content='{"title":',
        headers={"Content-Type": "application/json"},
    )

    assert response.status_code == 422


def test_oversized_request():
    response = client.post(
        "/todos",
        json={"title": "A" * (1024 * 1024 + 1)},
    )

    assert response.status_code == 413


def test_oversized_request_without_content_length():
    body = b'{"title":"' + b"A" * (1024 * 1024 + 1) + b'"}'

    def chunks():
        yield body[:500_000]
        yield body[500_000:]

    response = client.post(
        "/todos",
        content=chunks(),
        headers={"Content-Type": "application/json"},
    )

    assert response.status_code == 413
