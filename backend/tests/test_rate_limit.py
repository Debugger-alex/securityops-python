import os
from uuid import uuid4

import pytest
from fastapi import FastAPI, Request
from fastapi.testclient import TestClient
from slowapi import Limiter
from slowapi.errors import RateLimitExceeded
from slowapi.extension import _rate_limit_exceeded_handler
from slowapi.middleware import SlowAPIMiddleware
from slowapi.util import get_remote_address


@pytest.mark.skipif(
    not os.environ.get("RATE_LIMIT_STORAGE_URI", "").startswith(("redis://", "rediss://")),
    reason="Redis-Mehrinstanztest läuft in der PostgreSQL-/Redis-CI.",
)
def test_rate_limit_is_shared_between_independent_api_limiters() -> None:
    storage_uri = os.environ["RATE_LIMIT_STORAGE_URI"]
    path = f"/shared-rate-limit-{uuid4().hex}"

    def create_app() -> FastAPI:
        limiter = Limiter(key_func=get_remote_address, storage_uri=storage_uri)
        app = FastAPI()
        app.state.limiter = limiter
        app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
        app.add_middleware(SlowAPIMiddleware)

        @app.get(path)
        @limiter.limit("1/minute")
        def endpoint(request: Request) -> dict[str, str]:
            return {"status": "ok"}

        return app

    with TestClient(create_app()) as first_api, TestClient(create_app()) as second_api:
        assert first_api.get(path).status_code == 200
        assert second_api.get(path).status_code == 429
