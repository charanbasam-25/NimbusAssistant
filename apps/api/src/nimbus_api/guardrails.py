"""Input checks and ingestion-time flags for common prompt-injection risks."""

from __future__ import annotations

import base64
import ipaddress
import re
from dataclasses import dataclass
from urllib.parse import urlsplit

GUARDRAILS_VERSION = "guardrails-v1"
MAX_INPUT_CHARS = 1000

INJECTION_PATTERNS = tuple(
    re.compile(pattern, re.IGNORECASE | re.MULTILINE)
    for pattern in (
        r"\b(?:ignore|disregard|forget|override|bypass)\b(?:\W+\w+){0,3}?\W+(?:previous|prior|above|earlier|preceding|all|any|your|system|safety)\b(?:\W+\w+){0,2}?\W+(?:instructions?|rules|prompts?|directions|guidelines|guardrails|policies)\b",
        r"\b(?:reveal|show|print|repeat|output|display|leak)\b(?:\W+\w+){0,4}?\W+(?:system|hidden|initial|original)\W+(?:prompt|instructions|message)s?\b",
        r"\byou\s+are\s+now\s+(?:in\s+)?(?:an?\s+|the\s+)?(?:dan|developer|admin|administrator|root|god|jailbroken|unrestricted|unfiltered|evil)\b",
        r"\b(?:developer|admin|god|jailbreak)\s+mode\b",
        r"\b(?:pretend|imagine)\b(?:\W+\w+){0,4}?\W+(?:no|without)\W+(?:restrictions|rules|filters|guidelines|limitations|censorship)",
        r"^\s*(?:system|assistant)\s*:\s*(?:you\b|ignore\b|forget\b|disregard\b|always\b|never\b|from\s+now\b)",
    )
)
BASE64_RUN = re.compile(r"[A-Za-z0-9+/]{24,}={0,2}")
UNSAFE_SCHEME = re.compile(
    r"\b(?:file|gopher|dict|ldap)://|\bjavascript:(?!\s)|\bdata:[a-z]+/[a-z0-9.+-]+[;,]",
    re.IGNORECASE,
)
HTTP_URL = re.compile(r"https?://[^\s<>\"']+", re.IGNORECASE)
ABUSE = re.compile(
    r"\b(?:kill\s+yourself|kys|go\s+die|i\s+will\s+(?:kill|hurt)\s+you)\b", re.IGNORECASE
)
METADATA_HOSTS = {
    "169.254.169.254",
    "metadata.google.internal",
    "metadata",
    "100.100.100.200",
    "fd00:ec2::254",
}


@dataclass(frozen=True)
class GuardrailResult:
    allowed: bool
    reason: str | None = None


def looks_like_injection(text: str) -> bool:
    if any(pattern.search(text) for pattern in INJECTION_PATTERNS):
        return True
    for match in BASE64_RUN.finditer(text):
        try:
            decoded = base64.b64decode(match.group(0), validate=True)
        except (ValueError, base64.binascii.Error):
            continue
        if (
            decoded
            and sum(byte in (9, 10, 13) or 32 <= byte < 127 for byte in decoded) / len(decoded)
            > 0.9
        ):
            candidate = decoded.decode("ascii", errors="ignore")
            if any(pattern.search(candidate) for pattern in INJECTION_PATTERNS):
                return True
    return False


def _is_link_local_host(host: str) -> bool:
    normalized = host.rstrip(".").lower()
    try:
        address = ipaddress.ip_address(normalized)
    except ValueError:
        if normalized.isdecimal():
            try:
                address = ipaddress.IPv4Address(int(normalized))
            except (ipaddress.AddressValueError, ValueError):
                return False
        else:
            return False
    return address.is_link_local


def has_unsafe_url(text: str) -> bool:
    if UNSAFE_SCHEME.search(text):
        return True
    for match in HTTP_URL.finditer(text):
        candidate = match.group(0).rstrip(".,;:!?)")
        try:
            host = urlsplit(candidate).hostname
        except ValueError:
            continue
        if not host:
            continue
        normalized = host.lower().rstrip(".")
        if normalized in METADATA_HOSTS or _is_link_local_host(normalized):
            return True
    return False


def should_flag_chunk(text: str) -> bool:
    return looks_like_injection(text) or has_unsafe_url(text)


def check_input(text: str) -> GuardrailResult:
    """Reject suspicious user inputs, returning the first matching reason."""
    if not text.strip():
        return GuardrailResult(False, "empty")
    if len(text) > MAX_INPUT_CHARS:
        return GuardrailResult(False, "too_long")
    if looks_like_injection(text):
        return GuardrailResult(False, "prompt_injection")
    if has_unsafe_url(text):
        return GuardrailResult(False, "unsafe_url")
    if ABUSE.search(text):
        return GuardrailResult(False, "abuse")
    return GuardrailResult(True)
