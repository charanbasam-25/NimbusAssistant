"""Password hashing and short-lived Ed25519-signed Nimbus access tokens."""

from __future__ import annotations

import os
import time
from collections.abc import Mapping
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any
from uuid import uuid4

import jwt
from argon2 import PasswordHasher
from argon2.exceptions import InvalidHashError, VerificationError, VerifyMismatchError
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey

from nimbus_api.config import REPOSITORY_ROOT

_PASSWORD_HASHER = PasswordHasher()
_DUMMY_HASH = _PASSWORD_HASHER.hash("nimbus-unknown-account-dummy-password")


@dataclass(frozen=True)
class TokenSettings:
    public_key_pem: str
    private_key_pem: str | None = None
    issuer: str = "nimbus-api"
    audience: str = "nimbus-web"
    ttl_seconds: int = 1800
    leeway_seconds: int = 10


def generate_keypair() -> tuple[str, str]:
    """Return an Ed25519 private PKCS8 PEM and public SubjectPublicKeyInfo PEM."""
    private_key = Ed25519PrivateKey.generate()
    private_pem = private_key.private_bytes(
        serialization.Encoding.PEM,
        serialization.PrivateFormat.PKCS8,
        serialization.NoEncryption(),
    )
    public_pem = private_key.public_key().public_bytes(
        serialization.Encoding.PEM,
        serialization.PublicFormat.SubjectPublicKeyInfo,
    )
    return private_pem.decode("ascii"), public_pem.decode("ascii")


def load_token_settings(
    env: Mapping[str, str] | None = None, base_dir: Path = REPOSITORY_ROOT
) -> TokenSettings:
    """Load token keys from configured files; key loading remains lazy for guests."""
    settings = os.environ if env is None else env
    public_path = Path(settings.get("JWT_PUBLIC_KEY_PATH", "secrets/jwt_ed25519.pub"))
    private_path = Path(settings.get("JWT_PRIVATE_KEY_PATH", "secrets/jwt_ed25519.pem"))
    if not public_path.is_absolute():
        public_path = base_dir / public_path
    if not private_path.is_absolute():
        private_path = base_dir / private_path
    public_pem = public_path.read_text(encoding="ascii")
    private_pem = private_path.read_text(encoding="ascii") if private_path.is_file() else None
    return TokenSettings(
        public_key_pem=public_pem,
        private_key_pem=private_pem,
        issuer=settings.get("JWT_ISSUER", "nimbus-api"),
        audience=settings.get("JWT_AUDIENCE", "nimbus-web"),
    )


def hash_password(password: str) -> str:
    """Hash a password with Argon2id using the library's current safe defaults."""
    return _PASSWORD_HASHER.hash(password)


def verify_password(password: str, encoded_hash: str) -> bool:
    """Verify an Argon2 hash, treating malformed stored hashes as a mismatch."""
    try:
        return _PASSWORD_HASHER.verify(encoded_hash, password)
    except (VerifyMismatchError, VerificationError, InvalidHashError):
        return False


def authenticate(connection: Any, email: str, password: str) -> tuple[Any, str, str] | None:
    """Look up a normalized address and verify its hash without an account oracle."""
    normalized_email = email.strip().lower()
    row = connection.execute(
        "SELECT id, role, home_region, password_hash FROM users WHERE lower(email) = %s",
        (normalized_email,),
    ).fetchone()
    if row is None:
        verify_password(password, _DUMMY_HASH)
        return None
    if not verify_password(password, row[3]):
        return None
    return row[0], row[1], row[2]


def _timestamp(value: datetime | float | None) -> int:
    if value is None:
        return int(time.time())
    if isinstance(value, datetime):
        return int(value.timestamp())
    return int(value)


def issue_token(
    settings: TokenSettings,
    user_id: str | Any,
    role: str,
    region: str | None,
    now: datetime | float | None = None,
) -> str:
    if not settings.private_key_pem:
        raise RuntimeError("JWT private key is not configured")
    if role not in {"user", "admin"} or region not in {"R1", "R2"}:
        raise ValueError("role and region must identify a supported Nimbus user")
    issued_at = _timestamp(now)
    claims = {
        "sub": str(user_id),
        "role": role,
        "region": region,
        "iss": settings.issuer,
        "aud": settings.audience,
        "iat": issued_at,
        "exp": issued_at + settings.ttl_seconds,
        "jti": str(uuid4()),
    }
    return jwt.encode(claims, settings.private_key_pem, algorithm="EdDSA")


def verify_token(settings: TokenSettings, token: str) -> dict[str, Any]:
    """Verify signature and registered claims, then validate Nimbus role/region."""
    options: dict[str, Any] = {
        "require": ["sub", "role", "region", "iss", "aud", "iat", "exp"],
    }
    decode_options: dict[str, Any] = {
        "algorithms": ["EdDSA"],
        "audience": settings.audience,
        "issuer": settings.issuer,
        "leeway": settings.leeway_seconds,
        "options": options,
    }
    claims = jwt.decode(token, settings.public_key_pem, **decode_options)
    if claims.get("role") not in {"user", "admin"} or claims.get("region") not in {"R1", "R2"}:
        raise jwt.InvalidTokenError("unsupported Nimbus role or region")
    return claims
