# Regional-source interoperability audit

Date: 2026-08-03 UTC

## Objective

Identify a deterministic official export route for SciELO and LILACS/BVS before either source is counted as formally searched.

## Search-interface probe

The official SciELO, BVS and LILACS search interfaces returned HTTP 403 to GitHub-hosted runners. The workflow did not attempt to evade the restriction, change identity, rotate addresses or bypass access controls.

Status:

- SciELO search interface: automated export blocked; assisted browser export required.
- BVS portal: automated export blocked; assisted browser export required.
- LILACS-filtered BVS search: automated export blocked; assisted browser export required.

## SciELO ArticleMeta API

The source code of the official `scieloorg/articlemetaapi` client confirmed the following endpoints:

- `/api/v1/articles`
- `/api/v1/article/identifiers`

The API is active and reported 1,422,573 article objects across the network and 560,811 identifiers in the `scl` collection at the time of the probe.

However, ArticleMeta is a metadata/harvesting service, not a full-text search service. Supplying `q=progressive pulmonary fibrosis` to `/api/v1/articles` did not alter the API filter or total. It returned the same global total and the first 100 chronological/processing records. Therefore the `q` parameter was ignored and ArticleMeta cannot be used as the formal SciELO search mechanism.

ArticleMeta remains suitable for metadata enrichment after SciELO PIDs have been identified through the official search export.

## Required assisted export

A human-operated browser must execute and export the exact multilingual strategy from:

- `https://search.scielo.org/` in RIS or CSV, all results;
- `https://pesquisa.bvsalud.org/portal/` with the LILACS database filter, in RIS or CSV, all results.

The export files must be preserved unchanged with:

- exact query;
- platform and database selection;
- date/time and timezone;
- displayed hit count;
- raw RIS/CSV file;
- SHA-256 digest;
- screenshot or PDF of the final search page;
- notes about any platform maximum or pagination.

## Methodological status

Neither SciELO nor LILACS/BVS is counted as executed yet. No eligibility decisions were created and no PRISMA count was changed.

## Technical evidence

GitHub Actions runs:

- regional interface probe: `30785916174` and follow-up runs;
- ArticleMeta probe: `30786009806`, corrected endpoint run `30786088857`.

Artifacts:

- `pfild-regional-sources-export-probe`
- `pfild-scielo-articlemeta-probe`
