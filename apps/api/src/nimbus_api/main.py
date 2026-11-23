"""Nimbus API routes with lazy EdDSA authentication and access-scoped search."""

from __future__ import annotations

import os
from collections.abc import Iterator
from typing import Annotated, Any

import jwt
import psycopg
from fastapi import Depends, FastAPI, Header, HTTPException
from pydantic import BaseModel, ConfigDict, Field

from nimbus_api.access import Persona, persona_from_claims
from nimbus_api.auth import (
    TokenSettings,
    authenticate,
    issue_token,
    load_token_settings,
    verify_token,
)
from nimbus_api.config import REPOSITORY_ROOT, database_url
from nimbus_api.guardrails import check_input
from nimbus_api.retrieval import search_chunks

app = FastAPI(title="Nimbus Support Assistant API", version="0.1.0")


@app.get("/health/live", tags=["health"])
async def liveness() -> dict[str, str]:
    """Confirm that the API process is accepting requests."""
    return {"status": "ok"}


def get_db_connection() -> Iterator[psycopg.Connection[Any]]:
    """Yield one database connection, translating connection failures to 503."""
    try:
        with psycopg.connect(database_url()) as connection:
            yield connection
    except psycopg.Error as error:
        raise HTTPException(status_code=503, detail="Database is unavailable") from error


def get_token_settings() -> TokenSettings:
    """Load keys only for routes that need token signing or verification."""
    return load_token_settings(os.environ, base_dir=REPOSITORY_ROOT)


def _unauthorized() -> HTTPException:
    """Return a fresh challenge exception for every invalid credential."""
    return HTTPException(
        status_code=401,
        detail="Invalid or expired bearer token",
        headers={"WWW-Authenticate": "Bearer"},
    )


def current_claims(
    authorization: Annotated[str | None, Header()] = None,
) -> dict[str, Any] | None:
    """Treat absent credentials as guest, but never downgrade a bad credential."""
    if authorization is None:
        return None
    scheme, separator, token = authorization.partition(" ")
    if not separator or scheme.lower() != "bearer" or not token.strip():
        raise _unauthorized()
    try:
        settings = get_token_settings()
        return verify_token(settings, token.strip())
    except (jwt.PyJWTError, OSError, RuntimeError, ValueError) as error:
        raise _unauthorized() from error


class LoginRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    email: str = Field(min_length=1, max_length=320)
    password: str = Field(min_length=1, max_length=1024)


class RetrievalRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    query: str = Field(min_length=3, max_length=1000)
    limit: int = Field(default=5, ge=1, le=20)


def validate_retrieval_request(request: RetrievalRequest) -> RetrievalRequest:
    """Reject guarded queries before resolving a database connection."""
    guardrail = check_input(request.query)
    if not guardrail.allowed:
        raise HTTPException(status_code=422, detail=guardrail.reason)
    return request


@app.post("/auth/login", tags=["auth"])
def login(
    request: LoginRequest,
    connection: Annotated[psycopg.Connection[Any], Depends(get_db_connection)],
) -> dict[str, str | int]:
    """Check a user's password and return a short-lived EdDSA bearer token."""
    user = authenticate(connection, request.email, request.password)
    if user is None:
        raise HTTPException(status_code=401, detail="Invalid email or password")
    try:
        settings = get_token_settings()
        token = issue_token(settings, user[0], user[1], user[2])
    except (OSError, RuntimeError, ValueError) as error:
        raise HTTPException(status_code=503, detail="Authentication is unavailable") from error
    return {
        "access_token": token,
        "token_type": "bearer",
        "expires_in": settings.ttl_seconds,
    }


@app.get("/me", tags=["auth"])
def me(
    claims: Annotated[dict[str, Any] | None, Depends(current_claims)],
) -> dict[str, Any]:
    """Describe the verified caller's persona without disclosing credentials."""
    if claims is None:
        return {"persona": "guest"}
    persona: Persona = persona_from_claims(claims)
    return {
        "persona": persona,
        "user_id": claims["sub"],
        "role": claims["role"],
        "region": claims["region"],
        "expires_at": claims["exp"],
    }


@app.post("/v1/retrieval/search", tags=["retrieval"])
def retrieve(
    request: Annotated[RetrievalRequest, Depends(validate_retrieval_request)],
    claims: Annotated[dict[str, Any] | None, Depends(current_claims)],
    connection: Annotated[psycopg.Connection[Any], Depends(get_db_connection)],
) -> dict[str, object]:
    """Search only the evidence visible to the verified caller's persona."""
    try:
        persona = persona_from_claims(claims)
        results = search_chunks(connection, request.query, persona, request.limit)
    except ValueError as error:
        raise HTTPException(status_code=422, detail=str(error)) from error
    return {"query": request.query, "persona": persona, "results": results}
