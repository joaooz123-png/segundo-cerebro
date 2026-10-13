# Regional sources status and assisted-export protocol

Last methodological update: 2026-10-13.

## Current status

Automated retrieval from the official LILACS/BVS and SciELO search interfaces has been tested from GitHub Actions. Both interfaces returned HTTP 403 to the automated runner. The resilient regional-source workflow records this as a source-access limitation instead of treating zero parsed records as a valid zero-result search.

Historical reproducibility evidence:
- GitHub Actions run: 33934797049
- execution time: 2026-09-05T01:00:29Z
- LILACS/BVS status: blocked_http_403
- SciELO status: blocked_http_403
- automated regional records accepted as search output: 0
- human eligibility decisions created: 0
- PRISMA decisions created: 0
- artifact digest: sha256:873287d04200cec275bac901b6f8cdf5c9da99b59ade0efdc4c970a06315e66f

This does **not** mean that LILACS or SciELO contain zero eligible records. It means the automated route is blocked and the searches remain incomplete until an assisted/manual export is imported.

## Frozen search architecture

The executable strategy is stored in:
`projects/pfild-ppf-systematic-review/scripts/collect_regional_open_sources_v3.py`

It contains three strata:
1. modern multilingual PF-ILD/PPF phrases;
2. acronym recall (PF-ILD, PFILD, and context-bound PPF);
3. multilingual concept recall combining ILD + fibrosis/fibrosing/fibrotic + progression.

Languages represented in search terms: English, Portuguese and Spanish.

No language, date, publication-type or study-design restriction is permitted during retrieval.

## Required assisted export — LILACS/BVS

Official interface: https://pesquisa.bvsalud.org/portal/

Requirements:
1. run each of the three frozen search strata separately;
2. apply the **LILACS database filter only**;
3. do not add language, year, document-type or study-design limits;
4. record local execution date/time, complete query, interface, result count and any filters;
5. export all records in RIS or CSV;
6. preserve the source-native export unchanged;
7. do not screen or deduplicate during export.

## Required assisted export — SciELO

Official interface: https://search.scielo.org/

Requirements:
1. run each frozen stratum using the `subject:` field, which searches title, abstract and keywords;
2. do not restrict collection, language, year or document type;
3. record local execution date/time, complete query and result count;
4. export all records in RIS or CSV;
5. preserve the source-native export unchanged;
6. do not screen or deduplicate during export.

## Import governance

After the source-native exports are available:
- ingest them without modification;
- retain LILACS/BVS and SciELO as separate provenance sources;
- match to the 2,767-PMID PubMed union by exact DOI and exact normalized title only as candidate links;
- never merge on DOI alone if title, PMID, document type or version conflicts;
- preserve preprints, protocols, letters, corrections, translations and journal articles as separate reports;
- send uncertain source-representation matches to human review;
- do not alter PRISMA counts until the regional searches are actually completed and the inter-source deduplication is frozen.

## Interpretation

Gate G2 remains **open** for regional databases. The access barrier is documented and reproducible, but documentation of a barrier is not a substitute for executing the source search.
