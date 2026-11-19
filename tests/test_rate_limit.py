from fastapi import FastAPI, Request
from fastapi.testclient import TestClient
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.util import get_remote_address


def test_rate_limit_blocks_excess_requests():
    test_app = FastAPI()

    limiter = Limiter(key_func=get_remote_address)
    test_app.state.limiter = limiter
    test_app.add_exception_handler(
        RateLimitExceeded,
        _rate_limit_exceeded_handler,
    )

    @test_app.get("/test-rate-limit")
    @limiter.limit("60/minute")
    def limited_endpoint(request: Request):
        return {"status": "ok"}

    with TestClient(test_app) as client:
        statuses = [
            client.get("/test-rate-limit").status_code
            for _ in range(61)
        ]

    assert statuses[:60] == [200] * 60
    assert statuses[60] == 429


def test_health_is_not_rate_limited():
    from app.main import app

    with TestClient(app) as client:
        statuses = [
            client.get("/health").status_code
            for _ in range(65)
        ]

    assert all(status == 200 for status in statuses)