# Assisted regional-source export protocol

Status: active fallback required because the official SciELO and BVS/LILACS search interfaces return HTTP 403 to GitHub-hosted runners. This is an access-path limitation, not evidence of zero results.

## Governance

- The regional searches are **not considered formally executed** until raw exports and result-count evidence are captured from a normal browser session.
- No automated 403 response may be interpreted as an empty result set.
- No eligibility or PRISMA decision is created by this protocol.
- Preserve source provenance separately for SciELO and LILACS/BVS even when both expose the same report.

## SciELO

1. Open `https://search.scielo.org/` in a normal browser.
2. Paste the complete contents of `scielo_multilingual_query.txt`.
3. Do not apply language, year, country, document-type or collection restrictions.
4. Record the displayed total before export.
5. Export **all references** in RIS and CSV when both formats are offered.
6. If the interface imposes a 2,000-record maximum, export deterministic year partitions and document each partition.
7. Save a screenshot or print-to-PDF of the final results page showing the exact query and total.

SciELO's current interface supports indexed searching and export in RIS, BibTeX, citation and CSV formats; all references can be exported up to the interface limit.

## LILACS/BVS

1. Open `https://pesquisa.bvsalud.org/portal/`.
2. Paste the complete contents of `lilacs_multilingual_query.txt`.
3. Apply **only** the database/collection filter **LILACS**. For reproducibility, the corresponding portal parameter is `filter[db][]=LILACS`; do not use the generic `filter=db:LILACS` form.
4. Do not apply language, date, publication-type or full-text filters.
5. Record the displayed total before export.
6. Export all references in RIS and CSV when available.
7. If pagination or export limits apply, use deterministic partitions and record them.
8. Save a screenshot or print-to-PDF showing the exact query, LILACS restriction and total.

BVS/iAHx supports database-specific filtering and export of retrieved references. The raw export, not an automated HTTP probe, is the source of truth for formal completion.

## Required file naming

- `scielo_pfild_ppf_YYYY-MM-DD_all.ris`
- `scielo_pfild_ppf_YYYY-MM-DD_all.csv`
- `scielo_pfild_ppf_YYYY-MM-DD_search.pdf`
- `lilacs_pfild_ppf_YYYY-MM-DD_all.ris`
- `lilacs_pfild_ppf_YYYY-MM-DD_all.csv`
- `lilacs_pfild_ppf_YYYY-MM-DD_search.pdf`

For partitions, append `_YYYY-YYYY` before the extension.

## Import controls

For every file, record:

- platform and database;
- exact query file and Git commit;
- local date, time and timezone;
- displayed hit count;
- number of exported rows/records;
- file size;
- SHA-256 digest;
- any warning or export limit;
- identity of the person who executed the export.

Never edit raw RIS/CSV files. Any cleaning or normalization must create a derived file with a separate checksum.

## Reconciliation after export

1. Import each source independently.
2. Compare against the 2,767-PMID PubMed candidate union by exact PMID/DOI/title only as machine suggestions.
3. Compare LILACS and SciELO to each other while preserving both provenance records.
4. Keep preprints, corrections, letters, protocols, translations and journal articles as distinct reports unless a human confirms they are the same source representation.
5. Route all regional-only records to the human screening queue.

## Methodological effect

The searches become formally executed only after raw exports and evidence files are present and reconciled. Until then, Gate G2 remains open for these two sources.
