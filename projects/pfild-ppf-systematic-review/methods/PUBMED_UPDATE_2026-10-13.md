# PubMed update search — 2026-10-13

## Purpose

The validated PubMed v2.2 strategy was rerun unchanged before human eligibility screening to capture records newly published or indexed since the August search. This is an update-search layer; it does not retrospectively alter the frozen historical August export.

## Search result

- database/platform: PubMed/MEDLINE via NCBI E-utilities;
- strategy: `search/pubmed_v2_candidate.txt`, unchanged v2.2;
- controlled v2.2 stratum: **2,717 unique PMIDs**;
- legacy safety stratum: 1,004 PMIDs;
- overlap: 866;
- legacy-only: 138;
- v2.2-only: 1,851;
- refreshed candidate union: **2,855 unique PMIDs**;
- PubMed-applicable sentinels: **62/62 recovered**;
- refreshed union PMID-order SHA-256: `a35b8447a0c9d9ca7048699acd7c15f3e655917cd06ab3928b39230094875946`.

Compared with the prior 2,767-PMID union:

- **88 PMIDs were added**;
- **0 prior PMIDs were lost**.

## Character of the 88-record update set

Automated prioritization is for review ordering only and is not an eligibility decision.

- publication year 2026: 84;
- other years represented: 2025, 2024, 2023 and 2018;
- high-priority by explicit PPF/PF-ILD title terminology: 27;
- medium priority: 24;
- broad/low-priority safety records: 37.

The update includes recent literature on connective-tissue-disease-associated PPF, systemic autoimmune rheumatic disease, rheumatoid arthritis, inflammatory myopathy, sarcoidosis, quantitative CT, biomarkers, pulmonary hypertension, delayed diagnosis, real-world recognition/treatment and emerging therapeutic trials.

## Refreshed enrichment and linked-source results

After the PubMed update, Europe PMC and ClinicalTrials.gov were refreshed before boundary recomputation.

### PubMed enrichment

- 2,855/2,855 metadata rows recovered;
- complete EFetch: 2,849;
- ESummary fallback: 6;
- with abstract: 2,581;
- with DOI: 2,702;
- with PMCID: 1,374.

### Europe PMC

- 1,192 records;
- 1,129 exact PMID source-representation matches to PubMed;
- 63 records without a matching PMID in the refreshed PubMed union.

### ClinicalTrials.gov and publication-linked registries

- 152 unique NCTs from direct terminological queries;
- 176 registry-identifier mentions in PubMed metadata;
- 72 unique NCTs mentioned;
- 13 already present in the direct NCT set;
- 59 additional publication-linked NCTs recovered;
- recovery failures: 0.

### Boundary/family layer

- 42 Europe PMC–PubMed boundary candidate pairs;
- 25 preprint → published-report family candidates;
- 7 exact-duplicate candidates;
- 3 same-report-or-family candidates;
- 7 weak-similarity/context-only pairs;
- 27 Europe PMC non-PubMed records had no candidate above the boundary threshold.

## Reproducibility

Sequential post-update union enrichment:

- GitHub Actions run: `38397412464`;
- artifact: `11812303667`;
- artifact digest: `sha256:999cd33bef5ffc23fd2504e7eac35baec381ebe7516b921f9e69292e5bd58035`.

## Governance

- automated eligibility decisions created: **0**;
- human eligibility decisions created: **0**;
- PRISMA decisions created: **0**;
- external independent PRESS review remains required;
- final cross-source duplicate/family confirmation remains human.
