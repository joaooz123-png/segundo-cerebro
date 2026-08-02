# Repository instructions for GitHub Copilot

## Protected project scope

The PF-ILD/PPF systematic evidence census lives under `projects/pfild-ppf-systematic-review/`.

When a task concerns PF-ILD, PFILD, progressive fibrosing/fibrotic interstitial lung disease, progressive fibrotic phenotype, or progressive pulmonary fibrosis in non-IPF ILD:

1. Read `projects/pfild-ppf-systematic-review/STATUS.md`, `AGENTS.md`, and `data/project_state.json` before editing.
2. Treat the 1,004 PubMed PMIDs and 66 discovery seeds as the current reproducible snapshot dated 2026-08-02.
3. Never alter raw source records silently. Preserve provenance and write corrected or enriched values as explicit updates with an audit note.
4. Distinguish bibliographic duplicates from multiple reports belonging to the same study or publication family.
5. Keep historical PF-ILD definitions analytically distinct from the 2022 ATS/ERS/JRS/ALAT PPF criteria.
6. Do not make autonomous final inclusion or exclusion decisions. AI output is a recommendation requiring human confirmation.
7. Do not invent authors, DOI, PMID, ISBN, registry IDs, result counts, pagination, access status, search dates, or full-text findings.
8. Preserve every author in structured data. Render six authors followed by `et al.` only when producing a Vancouver reference.
9. Do not use Sci-Hub, bypass paywalls, or add instructions for copyright circumvention. Record lawful retrieval attempts and unresolved access.
10. The PRISMA flow may change only from reproducible source exports and documented deduplication or screening decisions.

## Working style

- Prefer small, auditable commits.
- Record the exact source, date, query, result count, and exported identifier set for every formal search.
- Use JSON or CSV for machine-readable evidence data and Markdown for protocols, decisions, and audit reports.
- When uncertain, flag the record for human review rather than forcing a conclusion.
- Do not modify unrelated projects in this repository.
