# tests/test_quick_refresh.py
from fastapi.testclient import TestClient
from app.main import app

BASE = "/token"


def test_quick_refresh_flow(client: TestClient):
    # initial login (client is the TestClient fixture)
    r = client.post(f"{BASE}", json={"username": "test@example.com", "password": "abc12345"})
    assert r.status_code == 200
    assert client.cookies.get("refresh_token") is not None

    old_refresh = client.cookies.get("refresh_token")

    # rotate (same client) -> should succeed and set a new refresh cookie
    r2 = client.post(f"{BASE}/refresh")
    assert r2.status_code == 200
    new_refresh = client.cookies.get("refresh_token")
    assert new_refresh is not None
    assert new_refresh != old_refresh

    # simulate reuse attempt from another session: set old cookie on a fresh TestClient
    with TestClient(app) as other:
        other.cookies.set("refresh_token", old_refresh, domain="127.0.0.1", path="/")
        r3 = other.post(f"{BASE}/refresh")
        # old token was revoked during rotation -> reuse attempt must be rejected
        assert r3.status_code == 401
