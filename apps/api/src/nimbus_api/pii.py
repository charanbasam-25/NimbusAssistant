"""Conservative PII masking for corpus text before it reaches storage."""

from __future__ import annotations

import re
from dataclasses import dataclass

PII_VERSION = "pii-v1"

SECRET = re.compile(
    r"\b(?:sk-[A-Za-z0-9_-]{16,}|gsk_[A-Za-z0-9]{20,}|AIza[0-9A-Za-z_-]{35}|ghp_[A-Za-z0-9]{36}|AKIA[0-9A-Z]{16}|[A-Fa-f0-9]{32,})\b"
)
EMAIL = re.compile(r"\b[A-Za-z0-9._%+-]+@([A-Za-z0-9-]+(?:\.[A-Za-z0-9-]+)*\.[A-Za-z]{2,})\b")
IBAN = re.compile(r"\b[A-Z]{2}\d{2}(?: ?[A-Z0-9]{4}){2,7}(?: ?[A-Z0-9]{1,4})?\b")
CARD = re.compile(r"\b\d(?:[ -]?\d){12,18}\b")
PHONE = re.compile(
    r"\+\d{1,3}[\s.-]?\(?\d{1,4}\)?(?:[\s.-]?\d{2,5}){2,4}(?!\d)|(?:\(\d{3}\)\s?|\b\d{3}[\s.-])\d{3}[\s.-]\d{4}\b|\b[6-9]\d{9}\b"
)


@dataclass(frozen=True)
class MaskResult:
    text: str
    counts: dict[str, int]


def _luhn_valid(value: str) -> bool:
    digits = [int(character) for character in value if character.isdigit()]
    if not 13 <= len(digits) <= 19:
        return False
    checksum = 0
    parity = len(digits) % 2
    for index, digit in enumerate(digits):
        if index % 2 == parity:
            digit *= 2
            if digit > 9:
                digit -= 9
        checksum += digit
    return checksum % 10 == 0


def _iban_valid(value: str) -> bool:
    compact = re.sub(r"\s", "", value)
    if not 15 <= len(compact) <= 34:
        return False
    rearranged = compact[4:] + compact[:4]
    remainder = 0
    for character in rearranged:
        expanded = str(int(character)) if character.isdigit() else str(ord(character) - 55)
        for digit in expanded:
            remainder = (remainder * 10 + int(digit)) % 97
    return remainder == 1


def mask_pii(text: str) -> MaskResult:
    """Mask secrets, emails, valid IBANs/cards, then phone numbers."""
    counts: dict[str, int] = {}

    def replace(pattern: re.Pattern[str], kind: str, callback) -> None:
        nonlocal text

        def counted(match: re.Match[str]) -> str:
            replacement = callback(match)
            if replacement != match.group(0):
                counts[kind] = counts.get(kind, 0) + 1
            return replacement

        text = pattern.sub(counted, text)

    replace(SECRET, "secret", lambda _match: "[SECRET]")

    def email_replacement(match: re.Match[str]) -> str:
        domain = match.group(1).lower()
        if any(
            domain == suffix or domain.endswith("." + suffix)
            for suffix in ("example.com", "example.org", "example.net")
        ):
            return match.group(0)
        return "[EMAIL]"

    replace(EMAIL, "email", email_replacement)
    replace(IBAN, "iban", lambda match: "[IBAN]" if _iban_valid(match.group(0)) else match.group(0))

    def card_replacement(match: re.Match[str]) -> str:
        prefix = text[: match.start()]
        if re.search(r"https?://[^\s\"']*$", prefix, re.IGNORECASE):
            return match.group(0)
        if re.search(r"isbn[-_][^\s\"']*$", prefix, re.IGNORECASE):
            return match.group(0)
        digits = re.sub(r"\D", "", match.group(0))
        return f"[CARD_****{digits[-4:]}]" if _luhn_valid(match.group(0)) else match.group(0)

    replace(
        CARD,
        "card",
        card_replacement,
    )
    replace(PHONE, "phone", lambda _match: "[PHONE]")
    return MaskResult(text=text, counts=counts)


def contains_pii(text: str) -> bool:
    """Return whether masking would change the supplied text."""
    return mask_pii(text).text != text
