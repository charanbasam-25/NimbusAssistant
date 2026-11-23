import pytest
from nimbus_api.pii import contains_pii, mask_pii


@pytest.mark.parametrize(
    ("value", "expected"),
    [
        ("4111 1111 1111 1111", "[CARD_****1111]"),
        ("5500-0000-0000-0004", "[CARD_****0004]"),
        ("4111 1111 1111 1112", "4111 1111 1111 1112"),
    ],
)
def test_masks_only_luhn_valid_cards(value, expected) -> None:
    assert mask_pii(value).text == expected


@pytest.mark.parametrize(
    ("value", "expected"),
    [
        ("jane.doe@gmail.com", "[EMAIL]"),
        ("johndoe@example.com", "johndoe@example.com"),
        ("jane@team.example.org", "jane@team.example.org"),
    ],
)
def test_masks_non_reserved_email_domains(value, expected) -> None:
    assert mask_pii(value).text == expected


@pytest.mark.parametrize(
    "value",
    [
        "+1 (415) 555-2671",
        "+91 98765 43210",
        "9876543210",
        "(415) 555-2671",
    ],
)
def test_masks_phone_numbers(value) -> None:
    assert mask_pii(value).text == "[PHONE]"


def test_masks_only_mod97_valid_iban() -> None:
    assert mask_pii("GB82 WEST 1234 5698 7654 32").text == "[IBAN]"
    assert mask_pii("GB00 WEST 1234 5698 7654 32").text == "GB00 WEST 1234 5698 7654 32"


def test_masks_secret_formats_in_order() -> None:
    result = mask_pii("sk-abcdefghijklmnop1234 and AKIAIOSFODNN7EXAMPLE")
    assert result.text == "[SECRET] and [SECRET]"
    assert result.counts == {"secret": 2}


def test_preserves_ordinary_technical_documentation() -> None:
    value = (
        "Run uvicorn on port 8000 with FastAPI 0.115.0, released 2024-09-17; "
        "see https://fastapi.tiangolo.com/tutorial/."
    )
    assert mask_pii(value).text == value


def test_reports_category_counts() -> None:
    result = mask_pii("a@x.org, b@y.org and 4111111111111111")
    assert result.text == "[EMAIL], [EMAIL] and [CARD_****1111]"
    assert result.counts == {"email": 2, "card": 1}


def test_does_not_mistake_isbn_or_url_identifiers_for_cards() -> None:
    value = "isbn-9780306406157 and https://example.org/activity-1234567890123456"
    assert mask_pii(value).text == value


@pytest.mark.parametrize(
    ("value", "expected"),
    [("Contact alice@gmail.com", True), ("Contact docs@example.com", False)],
)
def test_contains_pii(value, expected) -> None:
    assert contains_pii(value) is expected
