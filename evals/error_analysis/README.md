# Error coding

1. Sample 30–50 traces per run, including all judge fails and random passes.
2. Read each trace and write the first thing that went wrong in `open_note`.
3. Do not choose a category until the open note is written.
4. Group similar notes into categories (axial coding).
5. Record one stage: retrieval, generation, safety, access, or other.
6. Add an actionable `fix_idea`; avoid describing only the symptom.
7. Count categories by run in `codes.md` and prioritize the largest.
8. Fix one high-count category, then rerun the same benchmark.
9. Add every fixed failure as a golden or synthetic regression row.
10. Keep traces local under ignored `evals/traces/`; never paste raw text into
    logs or metrics.
11. For M11 review, use only PII-masked, admin-only records with 14-day
    deletion.
12. Error coding runs immediately after v0 and after later benchmark runs.
