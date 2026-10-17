"""F-05 regression tests: endpoint access policy, fail-closed auth, rate limiting.

Verifies (Phase 2, Priority 4 — F-05):
1. The documented access policy exists and classifies the live endpoints.
2. Protected routers carry the `require_api_key` dependency; public routers do not.
3. `require_api_key` fails closed: 503 when unconfigured, 401 when missing/invalid, 200 when valid.
4. The public `/circle-rates/lookup` route carries the rate limiter.
5. The rate limiter blocks beyond its window and can be reset.
"""

from __future__ import annotations

from pathlib import Path
from typing import Annotated

from fastapi import Depends, FastAPI
from fastapi.testclient import TestClient

from app.api import router as api_router_module
from app.api.circle_rates import router as circle_rates_router
from app.core.config import Settings, get_settings
from app.security.auth import AuthenticatedCaller, AuthService, require_api_key
from app.security.rate_limit import (
    SlidingWindowRateLimiter,
    enforce_rate_limit,
    limiter_for,
    reset_rate_limiters,
)

REPO_ROOT = Path(__file__).resolve().parents[3]

PROTECTED_ROUTERS = (
    api_router_module.auth_router,
    api_router_module.applications_router,
    api_router_module.documents_router,
    api_router_module.underwriting_router,
    api_router_module.compliance_router,
    api_router_module.reports_router,
)
PUBLIC_ROUTERS = (api_router_module.health_router, api_router_module.circle_rates_router)


def _settings(**overrides) -> Settings:
    return Settings(APP_ENV="test", _env_file=None, **overrides)


def _dependency_callables(router) -> set:
    return {dep.dependency for dep in router.dependencies}


# =========================================================================
# 1. Documented policy
# =========================================================================


def test_access_policy_is_documented() -> None:
    policy = REPO_ROOT / "docs" / "security" / "access_policy.md"
    assert policy.exists(), "F-05 requires the public/private decision to be documented"
    text = policy.read_text(encoding="utf-8")
    assert "/circle-rates/lookup" in text
    assert "/health" in text
    assert "accepted" in text.lower()


# =========================================================================
# 2. Protected-by-default router wiring
# =========================================================================


def test_protected_routers_require_api_key() -> None:
    for router in PROTECTED_ROUTERS:
        assert require_api_key in _dependency_callables(router), (
            f"protected router {router.prefix!r} must carry require_api_key"
        )


def test_public_routers_are_not_authenticated() -> None:
    for router in PUBLIC_ROUTERS:
        assert require_api_key not in _dependency_callables(router), (
            f"public router {router.prefix!r} must not require authentication by mistake"
        )


def test_public_lookup_route_carries_rate_limit() -> None:
    route = next(
        route
        for route in circle_rates_router.routes
        if getattr(route, "path", None) == "/circle-rates/lookup"
    )
    assert enforce_rate_limit in {dep.dependency for dep in route.dependencies}


# =========================================================================
# 3. Fail-closed authentication behaviour
# =========================================================================


def _protected_client(settings: Settings) -> TestClient:
    app = FastAPI()

    @app.get("/protected")
    async def protected_route(
        caller: Annotated[AuthenticatedCaller, Depends(require_api_key)],
    ):
        return {"subject": caller.subject}

    app.dependency_overrides[get_settings] = lambda: settings
    return TestClient(app)


def test_unconfigured_api_key_fails_closed_with_503() -> None:
    client = _protected_client(_settings(API_KEY=""))
    response = client.get("/protected")
    assert response.status_code == 503
    assert "not configured" in response.json()["detail"].lower()


def test_missing_credentials_returns_401() -> None:
    client = _protected_client(_settings(API_KEY="s3cret"))
    response = client.get("/protected")
    assert response.status_code == 401
    assert response.headers["www-authenticate"] == "Bearer"


def test_invalid_credentials_returns_401() -> None:
    client = _protected_client(_settings(API_KEY="s3cret"))
    response = client.get("/protected", headers={"Authorization": "Bearer wrong-key"})
    assert response.status_code == 401


def test_valid_bearer_credentials_are_accepted() -> None:
    client = _protected_client(_settings(API_KEY="s3cret"))
    response = client.get("/protected", headers={"Authorization": "Bearer s3cret"})
    assert response.status_code == 200
    assert response.json() == {"subject": "api-key"}


def test_valid_x_api_key_header_is_accepted() -> None:
    client = _protected_client(_settings(API_KEY="s3cret"))
    response = client.get("/protected", headers={"X-API-Key": "s3cret"})
    assert response.status_code == 200


# =========================================================================
# 4. Rate limiter behaviour
# =========================================================================


def test_sliding_window_blocks_beyond_limit() -> None:
    limiter = SlidingWindowRateLimiter(limit=2, window_seconds=60.0)
    assert limiter.check("client")[0] is True
    assert limiter.check("client")[0] is True
    allowed, retry_after = limiter.check("client")
    assert allowed is False
    assert retry_after >= 1
    # A different key is unaffected.
    assert limiter.check("other")[0] is True


def test_sliding_window_reset() -> None:
    limiter = SlidingWindowRateLimiter(limit=1, window_seconds=60.0)
    assert limiter.check("client")[0] is True
    assert limiter.check("client")[0] is False
    limiter.reset()
    assert limiter.check("client")[0] is True


def test_limiter_registry_is_resettable() -> None:
    reset_rate_limiters()
    first = limiter_for(7)
    assert limiter_for(7) is first  # shared per distinct limit
    reset_rate_limiters()
    assert limiter_for(7) is not first


def test_rate_limit_dependency_returns_429_when_exceeded() -> None:
    reset_rate_limiters()
    app = FastAPI()

    @app.get("/limited", dependencies=[Depends(enforce_rate_limit)])
    async def limited_route():
        return {"ok": True}

    app.dependency_overrides[get_settings] = lambda: _settings(RATE_LIMIT_PER_MINUTE=2)
    client = TestClient(app)

    assert client.get("/limited").status_code == 200
    assert client.get("/limited").status_code == 200
    throttled = client.get("/limited")
    assert throttled.status_code == 429
    assert int(throttled.headers["retry-after"]) >= 1
    reset_rate_limiters()


def test_rate_limit_zero_disables_limiting() -> None:
    reset_rate_limiters()
    app = FastAPI()

    @app.get("/limited", dependencies=[Depends(enforce_rate_limit)])
    async def limited_route():
        return {"ok": True}

    app.dependency_overrides[get_settings] = lambda: _settings(RATE_LIMIT_PER_MINUTE=0)
    client = TestClient(app)
    for _ in range(5):
        assert client.get("/limited").status_code == 200


# =========================================================================
# 5. AuthService primitives
# =========================================================================


def test_auth_service_verify() -> None:
    service = AuthService(_settings(API_KEY="abc123"))
    assert service.is_configured is True
    assert service.verify("abc123") is True
    assert service.verify("nope") is False
    assert service.verify(None) is False

    unconfigured = AuthService(_settings(API_KEY=""))
    assert unconfigured.is_configured is False
    assert unconfigured.verify("anything") is False
