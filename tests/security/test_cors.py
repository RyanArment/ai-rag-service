def test_cors_preflight_allows_configured_origin(client):
    response = client.options(
        "/health",
        headers={
            "Origin": "http://example.com",
            "Access-Control-Request-Method": "GET",
        },
    )

    assert response.status_code == 200
    assert response.headers.get("access-control-allow-origin") == "http://example.com"
    assert response.headers.get("access-control-allow-credentials") == "true"


def test_cors_preflight_blocks_unknown_origin(client):
    response = client.options(
        "/health",
        headers={
            "Origin": "http://not-allowed.example.com",
            "Access-Control-Request-Method": "GET",
        },
    )

    assert response.status_code == 200
    assert "access-control-allow-origin" not in response.headers
