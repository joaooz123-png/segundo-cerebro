# Assisted regional-source export protocol

Use this protocol only because the official SciELO and BVS/LILACS search interfaces block GitHub-hosted automation and no supported textual-search API was identified.

## SciELO

1. Open `https://search.scielo.org/` in a normal signed-in or local browser.
2. Paste the complete contents of `scielo_multilingual_query.txt`.
3. Do not apply language, year, country, document-type or collection restrictions.
4. Record the displayed total before export.
5. Export **all references** in RIS and CSV when both formats are offered.
6. If the interface imposes a 2,000-record maximum, export deterministic year partitions and document each partition.
7. Save a screenshot or print-to-PDF of the final results page showing the query and total.

## LILACS/BVS

1. Open `https://pesquisa.bvsalud.org/portal/`.
2. Paste the complete contents of `lilacs_multilingual_query.txt`.
3. Apply only the database/collection filter **LILACS**.
4. Do not apply language, date, publication-type or full-text filters.
5. Record the displayed total before export.
6. Export all references in RIS and CSV when available.
7. If pagination or export limits apply, use deterministic partitions and record them.
8. Save a screenshot or print-to-PDF showing the query, LILACS restriction and total.

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
- exact query version/commit;
- local date, time and timezone;
- displayed hit count;
- number of exported rows/records;
- file size;
- SHA-256 digest;
- any warning or export limit;
- identity of the person who executed the export.

Never edit raw RIS/CSV files. Any cleaning or normalization must create a derived file with a separate checksum.

## Methodological effect

The searches become formally executed only after raw exports and evidence files are present and reconciled. This protocol creates no eligibility decision and does not alter PRISMA counts by itself.
