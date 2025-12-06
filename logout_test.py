# logout_test.py
import os
import requests

BASE = os.environ.get("BASE", "http://127.0.0.1:8000")


def run_logout_test(base: str = BASE) -> None:
    s = requests.Session()
    r = s.post(f"{base}/token", json={"username": "test@example.com", "password": "abc12345"})
    print("LOGIN", r.status_code, r.text if r.text else "")

    # try get refresh cookie and access token
    refresh_cookie = s.cookies.get("refresh_token")
    access_token = None
    try:
        j = r.json()
        access_token = j.get("access_token")
    except Exception:
        access_token = None

    print("COOKIE:", (refresh_cookie[:20] + "...") if refresh_cookie else None)
    print("ACCESS_TOKEN (present):", bool(access_token))

    # Send logout. If access token available use it.
    headers = {}
    if access_token:
        headers["Authorization"] = f"Bearer {access_token}"

    r2 = s.post(f"{base}/logout", headers=headers)
    print("LOGOUT:", r2.status_code, r2.text if r2.text else "")

    # Optional: probe token row/events if you want (not included here)


if __name__ == "__main__":
    run_logout_test()
