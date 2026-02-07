from app.core.rate_limiter import RateLimiter
import app.core.rate_limiter as rate_limiter_module
import app.main as main


def test_rate_limiter_allows_within_limit():
    limiter = RateLimiter(max_requests=2, window_seconds=10)
    assert limiter.allow("client-1") is True
    assert limiter.allow("client-1") is True
    assert limiter.allow("client-1") is False


def test_rate_limiter_allows_after_window(monkeypatch):
    limiter = RateLimiter(max_requests=1, window_seconds=1)
    times = iter([0.0, 0.1, 1.2, 1.3])

    def fake_monotonic():
        return next(times)

    monkeypatch.setattr(rate_limiter_module.time, "monotonic", fake_monotonic)

    assert limiter.allow("client-1") is True
    assert limiter.allow("client-1") is False
    assert limiter.allow("client-1") is True


def test_rate_limit_middleware_blocks_after_limit(client):
    main.rate_limiter.max_requests = 2
    main.rate_limiter.window_seconds = 60
    main.rate_limiter._requests.clear()

    first = client.get("/_test")
    second = client.get("/_test")
    third = client.get("/_test")

    assert first.status_code == 200
    assert second.status_code == 200
    assert third.status_code == 429
