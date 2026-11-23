from run_access import build_cases, evaluate


def _fixture_documents():
    return [
        {
            "id": "refund-r1",
            "source_path": "public/refund-r1.md",
            "audience": "public",
            "region": "R1",
            "question": "What is the refund window?",
        },
        {
            "id": "refund-r2",
            "source_path": "public/refund-r2.md",
            "audience": "public",
            "region": "R2",
            "question": "What is the refund window?",
        },
        {
            "id": "runbook",
            "source_path": "internal/runbook.md",
            "audience": "internal",
            "region": "global",
            "question": "Which runbook identifier applies?",
        },
        {
            "id": "glossary",
            "source_path": "glossary.md",
            "audience": "public",
            "region": "global",
            "question": None,
        },
    ]


def test_ground_truth_cases_use_shared_questions_and_source_paths() -> None:
    cases = build_cases(_fixture_documents())

    assert len(cases) == 6
    guest_refund = next(
        case for case in cases if case["persona"] == "guest" and "refund" in case["query"]
    )
    r1_refund = next(
        case for case in cases if case["persona"] == "R1" and "refund" in case["query"]
    )
    assert guest_refund["expected_doc_ids"] == []
    assert set(guest_refund["forbidden_doc_ids"]) == {
        "public/refund-r1.md",
        "public/refund-r2.md",
    }
    assert r1_refund["expected_doc_ids"] == ["public/refund-r1.md"]
    assert r1_refund["forbidden_doc_ids"] == ["public/refund-r2.md"]


def test_correct_access_filter_has_no_leaks_and_full_expected_recall() -> None:
    cases = build_cases(_fixture_documents())
    all_docs = _fixture_documents()

    def search(query, persona, limit, query_mode):
        del limit, query_mode
        related = [doc for doc in all_docs if doc.get("question") == query]
        return [
            {
                "source_path": doc["source_path"],
                "classification": {
                    "audience": doc["audience"],
                    "region": doc["region"],
                },
            }
            for doc in related
            if (
                doc["audience"] == "public" and doc["region"] == "global"
                if persona == "guest"
                else doc["audience"] in {"public", "internal"}
                and doc["region"] in {"global", persona}
            )
        ]

    report = evaluate(cases, search)

    assert report["leaks"] == 0
    assert report["expected_doc_recall"] == 1.0


def test_deliberately_broken_filter_is_detected_for_every_persona() -> None:
    cases = build_cases(_fixture_documents())
    all_docs = _fixture_documents()[:3]

    def broken_search(query, persona, limit, query_mode):
        del query, persona, limit, query_mode
        return [
            {
                "source_path": doc["source_path"],
                "classification": {
                    "audience": doc["audience"],
                    "region": doc["region"],
                },
            }
            for doc in all_docs
        ]

    report = evaluate(cases, broken_search)

    assert report["leaks"] == 10
    assert report["leaks_by_persona"] == {"guest": 6, "R1": 2, "R2": 2}
