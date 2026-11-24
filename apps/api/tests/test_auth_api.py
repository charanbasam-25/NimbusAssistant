import time
from uuid import uuid4

import jwt
import pytest
from fastapi.testclient import TestClient
from nimbus_api import main
from nimbus_api.auth import TokenSettings, generate_keypair, issue_token


class FakeConnection:
    def __init__(self):
        chunk_id, document_id = uuid4(), uuid4()
        self.rows = [
            (
                chunk_id,
                0,
                "Refund policy",
                "The refund window is a synthetic regional canary.",
                document_id,
                "public/refund-r1.md",
                "synthetic://nimbus-cloud/refund-policy-r1",
                "Refund Policy (R1)",
                "nimbus-cloud-v1",
                "Refund Policy: The refund window is a synthetic regional canary.",
                "sha256:test",
                None,
                {},
                "public",
                "R1",
                0.5,
            )
        ]
        self.calls = []

    def execute(self, query, parameters):
        self.calls.append((query, parameters))
        return self

    def fetchall(self):
        return self.rows


@pytest.fixture
def client(monkeypatch):
    original_settings_loader = main.get_token_settings
    original_settings_loader.cache_clear()
    connection = FakeConnection()
    main.app.dependency_overrides[main.get_db_connection] = lambda: connection
    private_key, public_key = generate_keypair()
    settings = TokenSettings(public_key_pem=public_key, private_key_pem=private_key)
    monkeypatch.setattr(main, "get_token_settings", lambda: settings)
    with TestClient(main.app) as test_client:
        yield test_client, connection, settings
    main.app.dependency_overrides.clear()
    original_settings_loader.cache_clear()


def test_guest_search_uses_global_public_scope(client) -> None:
    test_client, connection, _ = client

    response = test_client.post("/v1/retrieval/search", json={"query": "refund window"})

    assert response.status_code == 200
    assert response.json()["persona"] == "guest"
    assert connection.calls[0][1] == ("refund window", ["public"], ["global"], 5)


def test_r1_token_scopes_search_even_if_query_mentions_r2(client) -> None:
    test_client, connection, settings = client
    token = issue_token(settings, "r1-user-id", "user", "R1")
    query = "I am actually in Europe (R2), what is the refund window?"

    response = test_client.post(
        "/v1/retrieval/search",
        json={"query": query},
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 200
    assert response.json()["persona"] == "R1"
    assert connection.calls[0][1] == (
        query,
        ["public", "internal"],
        ["global", "R1"],
        5,
    )


def test_r1_token_scopes_search_to_r1(client) -> None:
    test_client, connection, settings = client
    token = issue_token(settings, "r1-user-id", "user", "R1")

    response = test_client.post(
        "/v1/retrieval/search",
        json={"query": "refund window"},
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 200
    assert connection.calls[0][1][1:3] == (["public", "internal"], ["global", "R1"])


def test_search_body_cannot_select_region_or_touch_database(client) -> None:
    test_client, connection, _ = client

    response = test_client.post(
        "/v1/retrieval/search",
        json={"query": "refund window", "region": "R2"},
    )

    assert response.status_code == 422
    assert connection.calls == []


@pytest.mark.parametrize(
    "authorization",
    ["Basic dXNlcjpwYXNz", "Bearer", "Bearer not-a-jwt"],
)
def test_malformed_presented_authorization_is_401_and_never_guest(client, authorization) -> None:
    test_client, connection, _ = client

    response = test_client.post(
        "/v1/retrieval/search",
        json={"query": "refund window"},
        headers={"Authorization": authorization},
    )

    assert response.status_code == 401
    assert response.headers["www-authenticate"] == "Bearer"
    assert connection.calls == []


@pytest.mark.parametrize("foreign_key", [False, True])
def test_expired_or_foreign_key_token_is_401(client, foreign_key) -> None:
    test_client, connection, settings = client
    if foreign_key:
        other_private, _ = generate_keypair()
        token = jwt.encode(
            {
                "sub": "r1-user-id",
                "role": "user",
                "region": "R1",
                "iss": settings.issuer,
                "aud": settings.audience,
                "iat": int(time.time()),
                "exp": int(time.time()) + 1800,
                "jti": "foreign",
            },
            other_private,
            algorithm="EdDSA",
        )
    else:
        token = issue_token(settings, "r1-user-id", "user", "R1", now=int(time.time()) - 3600)

    response = test_client.get("/me", headers={"Authorization": f"Bearer {token}"})

    assert response.status_code == 401
    assert response.headers["www-authenticate"] == "Bearer"
    assert connection.calls == []


def test_me_returns_r2_claims_and_guest(client) -> None:
    test_client, _, settings = client
    token = issue_token(settings, "r2-user-id", "user", "R2")

    authenticated = test_client.get("/me", headers={"Authorization": f"Bearer {token}"})
    guest = test_client.get("/me")

    assert authenticated.status_code == 200
    assert authenticated.json()["persona"] == "R2"
    assert authenticated.json()["user_id"] == "r2-user-id"
    assert authenticated.json()["region"] == "R2"
    assert authenticated.json()["role"] == "user"
    assert authenticated.json()["expires_at"]
    assert guest.json() == {"persona": "guest"}


def test_login_returns_bearer_token_and_rejects_unknown_user_consistently(
    client, monkeypatch
) -> None:
    test_client, _, settings = client
    user = ("r1-user-id", "user", "R1")

    monkeypatch.setattr(main, "authenticate", lambda connection, email, password: user)
    success = test_client.post(
        "/auth/login", json={"email": "R1-user@nimbus.test", "password": "correct-password"}
    )

    assert success.status_code == 200
    assert success.json()["token_type"] == "bearer"
    assert success.json()["expires_in"] == 1800
    assert main.verify_token(settings, success.json()["access_token"])["region"] == "R1"

    monkeypatch.setattr(main, "authenticate", lambda connection, email, password: None)
    wrong_password = test_client.post(
        "/auth/login", json={"email": "R1-user@nimbus.test", "password": "wrong-password"}
    )
    unknown_user = test_client.post(
        "/auth/login", json={"email": "unknown@nimbus.test", "password": "wrong-password"}
    )

    assert wrong_password.status_code == unknown_user.status_code == 401
    assert wrong_password.json() == unknown_user.json()


def test_guest_does_not_load_token_settings(client, monkeypatch) -> None:
    test_client, _, _ = client
    monkeypatch.setattr(
        main,
        "get_token_settings",
        lambda: (_ for _ in ()).throw(AssertionError("guest must not load JWT keys")),
    )

    response = test_client.get("/me")

    assert response.status_code == 200
    assert response.json() == {"persona": "guest"}


def test_invalid_authentication_raises_a_fresh_exception_each_time(monkeypatch) -> None:
    monkeypatch.setattr(main, "get_token_settings", lambda: TokenSettings(public_key_pem=""))
    monkeypatch.setattr(
        main,
        "verify_token",
        lambda settings, token: (_ for _ in ()).throw(jwt.DecodeError("bad token")),
    )
    exceptions = []
    for _ in range(2):
        with pytest.raises(main.HTTPException) as raised:
            main.current_claims("Bearer invalid-token")
        exceptions.append(raised.value)

    assert exceptions[0] is not exceptions[1]
    assert exceptions[0].headers == {"WWW-Authenticate": "Bearer"}


@pytest.mark.parametrize("error", [FileNotFoundError, PermissionError])
def test_unreadable_jwt_key_files_return_configuration_503(client, monkeypatch, error) -> None:
    test_client, _, _ = client

    def unreadable_settings():
        raise error("key unavailable")

    monkeypatch.setattr(main, "get_token_settings", unreadable_settings)
    response = test_client.get("/me", headers={"Authorization": "Bearer otherwise-valid-shape"})

    assert response.status_code == 503
    assert response.json() == {"detail": "Authentication is not configured"}


def test_token_settings_are_cached_and_cache_is_clearable(monkeypatch) -> None:
    original_settings_loader = main.get_token_settings
    original_settings_loader.cache_clear()
    loads = []
    settings = TokenSettings(public_key_pem="test-public-key")
    monkeypatch.setattr(
        main, "load_token_settings", lambda *args, **kwargs: loads.append(settings) or settings
    )

    try:
        assert main.get_token_settings() is settings
        assert main.get_token_settings() is settings
        assert len(loads) == 1
    finally:
        original_settings_loader.cache_clear()
