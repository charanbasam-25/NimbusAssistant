"""Single source of truth for Nimbus persona-to-document access rules."""

from typing import Any, Literal

Persona = Literal["guest", "R1", "R2"]

PERSONA_ACCESS: dict[Persona, tuple[list[str], list[str]]] = {
    "guest": (["public"], ["global"]),
    "R1": (["public", "internal"], ["global", "R1"]),
    "R2": (["public", "internal"], ["global", "R2"]),
}


def persona_from_claims(claims: dict[str, Any] | None) -> Persona:
    """Map verified token claims to the one region persona they establish."""
    if claims is None:
        return "guest"
    region = claims.get("region")
    if region in {"R1", "R2"}:
        return region
    raise ValueError("token claims do not establish a supported region")


def can_see(persona: Persona, audience: str, region: str) -> bool:
    """Return whether this persona may retrieve the tagged document."""
    audiences, regions = PERSONA_ACCESS[persona]
    return audience in audiences and region in regions
