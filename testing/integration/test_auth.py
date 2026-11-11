"""Cookie authentication across the real login, auth dependency, and logout."""

import jwt

from app.config import get_settings


def test_login_and_logout_flow(client, accounts):
    response = client.post(
        "/login",
        data={"username": accounts.student.username, "password": accounts.password},
    )

    assert response.status_code == 303
    assert response.headers["location"] == "https://testserver/app"
    token = response.cookies.get("access_token")
    assert token
    assert client.cookies.get("access_token") == token
    settings = get_settings()
    payload = jwt.decode(
        token, settings.secret_key, algorithms=[settings.jwt_algorithm]
    )
    assert payload["sub"] == str(accounts.student.id)
    assert payload["role"] == "student"
    assert "exp" in payload

    # Verify that the returned cookie actually authenticates a later request.
    profile = client.get("/app/profile")
    assert profile.status_code == 200
    assert profile.template.name == "profile.html"
    assert profile.context["user"].id == accounts.student.id

    response = client.get("/logout")

    assert response.status_code == 303
    assert response.headers["location"] == "https://testserver/login"
    assert any(
        header.startswith("access_token=") and "max-age=0" in header.lower()
        for header in response.headers.get_list("set-cookie")
    )
    assert client.cookies.get("access_token") is None
    # The existing 401 handler renders this template with HTTP 200.
    denied = client.get("/app/profile")
    assert denied.template.name == "401.html"
    assert "Unauthorized" in denied.text
    assert "user" not in denied.context
