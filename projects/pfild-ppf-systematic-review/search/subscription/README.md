# Subscription-database search package

Purpose: preserve PRESS-ready translations of the validated PF-ILD/PPF concept architecture for databases that require institutional access. These strategies are preparation artifacts only; a database is not counted as searched until the exact query is executed on the named platform and the raw export, platform, date, hit count, and checksum are archived.

## Platforms

- Embase.com
- Scopus
- Web of Science Core Collection
- CINAHL on EBSCOhost
- Cochrane CENTRAL

## Non-negotiable controls

1. No language restriction.
2. No publication-year restriction.
3. No publication-type restriction at retrieval.
4. No automatic eligibility decision.
5. Preserve the platform-generated final query/search history and displayed hit count.
6. Export all available records in the richest bibliographic format offered; preserve the raw export unchanged.
7. Record database and platform separately (e.g. Embase database on Embase.com; CINAHL database on EBSCOhost).
8. If a query is modified after PRESS or pilot validation, create a new immutable version rather than overwriting the old one.

## Validation sequence

- syntax check on the target platform;
- verify known sentinel/reference retrieval where the database indexes the record;
- inspect 20–50 results across old/new terminology for unexpected mapping or truncation;
- record exact hit count;
- export raw results;
- SHA-256 the export;
- reconcile by source record ID, DOI, PMID and exact title without silent merging;
- keep report-to-study-family linkage separate from record deduplication.

## Status

Prepared for platform execution and external PRESS review. Not yet counted as completed searches.
