# Error-code taxonomy

Replace or refine these starter codes based on trace evidence. Counts are
recorded per run; do not fill them from memory or estimates.

| Category | Definition | Example trace ID | Counts per run |
| --- | --- | --- | --- |
| `wrong_page` | Retrieved a page unrelated to the question's answer. | — | — |
| `right_page_wrong_chunk` | Relevant page found, but the useful passage was missed. | — | — |
| `split_code_example` | Retrieval returned an incomplete or disconnected code example. | — | — |
| `ignores_context` | Answer contradicts or fails to use relevant retrieved context. | — | — |
| `over_abstains` | System abstains although the pinned docs contain an answer. | — | — |
| `under_abstains` | System answers despite insufficient or absent evidence. | — | — |
| `bad_citation` | Citation is missing, malformed, or does not support the claim. | — | — |
| `region_confusion` | Retrieval or answer crosses an audience/region access boundary. | — | — |

Allowed stages: `retrieval`, `generation`, `safety`, `access`, `other`.
