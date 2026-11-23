import base64
import json
import time

import jwt
import pytest
from nimbus_api.auth import (
    TokenSettings,
    authenticate,
    generate_keypair,
    hash_password,
    issue_token,
    verify_password,
    verify_token,
)


@pytest.fixture
def token_settings():
    private_key, public_key = generate_keypair()
    return TokenSettings(public_key_pem=public_key, private_key_pem=private_key)


def test_token_round_trip(token_settings) -> None:
    token = issue_token(token_settings, "user-123", "user", "R1")

    claims = verify_token(token_settings, token)

    assert claims["sub"] == "user-123"
    assert claims["region"] == "R1"
    assert claims["role"] == "user"
    assert claims["iss"] == "nimbus-api"
    assert claims["aud"] == "nimbus-web"
    assert claims["exp"] - claims["iat"] == 1800
    assert claims["jti"]


def test_expired_token_is_rejected(token_settings) -> None:
    token = issue_token(token_settings, "user-123", "user", "R1", now=int(time.time()) - 3600)

    with pytest.raises(jwt.ExpiredSignatureError):
        verify_token(token_settings, token)


def test_wrong_audience_is_rejected(token_settings) -> None:
    token = issue_token(token_settings, "user-123", "user", "R1")
    wrong_settings = TokenSettings(
        public_key_pem=token_settings.public_key_pem,
        audience="another-client",
    )

    with pytest.raises(jwt.InvalidAudienceError):
        verify_token(wrong_settings, token)


def test_wrong_issuer_is_rejected(token_settings) -> None:
    token = issue_token(token_settings, "user-123", "user", "R1")
    wrong_settings = TokenSettings(
        public_key_pem=token_settings.public_key_pem,
        issuer="another-issuer",
    )

    with pytest.raises(jwt.InvalidIssuerError):
        verify_token(wrong_settings, token)


def test_token_signed_by_another_key_is_rejected(token_settings) -> None:
    other_private, _ = generate_keypair()
    token = jwt.encode(
        {
            "sub": "user-123",
            "role": "user",
            "region": "R1",
            "iss": "nimbus-api",
            "aud": "nimbus-web",
            "iat": int(time.time()),
            "exp": int(time.time()) + 1800,
            "jti": "other-key",
        },
        other_private,
        algorithm="EdDSA",
    )

    with pytest.raises(jwt.InvalidSignatureError):
        verify_token(token_settings, token)


def test_edited_region_claim_fails_signature_validation(token_settings) -> None:
    token = issue_token(token_settings, "user-123", "user", "R1")
    header, encoded_payload, signature = token.split(".")
    claims = json.loads(
        base64.urlsafe_b64decode(encoded_payload + "=" * (-len(encoded_payload) % 4))
    )
    claims["region"] = "R2"
    edited_payload = base64.urlsafe_b64encode(json.dumps(claims).encode()).rstrip(b"=").decode()

    with pytest.raises(jwt.InvalidSignatureError):
        verify_token(token_settings, f"{header}.{edited_payload}.{signature}")


def test_only_eddsa_algorithm_is_allowed(token_settings) -> None:
    token = jwt.encode(
        {
            "sub": "user-123",
            "role": "user",
            "region": "R1",
            "iss": "nimbus-api",
            "aud": "nimbus-web",
            "iat": int(time.time()),
            "exp": int(time.time()) + 1800,
        },
        "not-an-ed25519-key-but-long-enough-for-hs256-testing",
        algorithm="HS256",
    )

    with pytest.raises(jwt.InvalidAlgorithmError):
        verify_token(token_settings, token)


def test_valid_signature_with_unsupported_region_is_rejected(token_settings) -> None:
    token = jwt.encode(
        {
            "sub": "user-123",
            "role": "user",
            "region": "R3",
            "iss": "nimbus-api",
            "aud": "nimbus-web",
            "iat": int(time.time()),
            "exp": int(time.time()) + 1800,
        },
        token_settings.private_key_pem,
        algorithm="EdDSA",
    )

    with pytest.raises(jwt.InvalidTokenError, match="unsupported Nimbus"):
        verify_token(token_settings, token)


@pytest.mark.parametrize("region", ["", None])
def test_issue_token_rejects_empty_region(token_settings, region) -> None:
    with pytest.raises(ValueError, match="region"):
        issue_token(token_settings, "user-123", "user", region)


def test_hashing_and_password_verification_handles_invalid_hash() -> None:
    password_hash = hash_password("correct-horse-battery")

    assert verify_password("correct-horse-battery", password_hash)
    assert not verify_password("wrong-password", password_hash)
    assert not verify_password("wrong-password", "not-an-argon2-hash")


class FakeUserConnection:
    def __init__(self, row):
        self.row = row
        self.query = None
        self.parameters = None

    def execute(self, query, parameters):
        self.query = query
        self.parameters = parameters
        return self

    def fetchone(self):
        return self.row


def test_authenticate_normalizes_email_and_handles_wrong_or_unknown_password() -> None:
    password_hash = hash_password("correct-horse-battery")
    connection = FakeUserConnection(("user-id", "user", "R1", password_hash))

    assert authenticate(connection, "  R1-USER@NIMBUS.TEST ", "correct-horse-battery") == (
        "user-id",
        "user",
        "R1",
    )
    assert connection.parameters == ("r1-user@nimbus.test",)
    assert authenticate(connection, "r1-user@nimbus.test", "wrong-password") is None
    missing = FakeUserConnection(None)
    assert authenticate(missing, "unknown@nimbus.test", "wrong-password") is None
