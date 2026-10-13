# G3 registry-linked publication-family map v2

Generated: 2026-10-13  
Status: internally derived candidate family map after the 2,855-PMID PubMed refresh; human confirmation pending

## Purpose

Create reproducible **report → registry → study-family candidate** links without merging bibliographic reports.

Input layers:

1. refreshed PubMed union registry identifiers extracted from **2,855** enriched records;
2. OpenAlex explicit supplementary candidates;
3. formal citation-chasing candidates.

Only an **explicit registry identifier** creates a link in this layer. Title similarity alone is not used here.

## Current internally derived result

- candidate registry-linked families: **116**
- explicit report–registry links: **236**
- NCT families: **87**
- UMIN families: **10**
- EudraCT families: **5**
- jRCT families: **5**
- DRKS families: **4**
- ChiCTR families: **3**
- ISRCTN families: **2**
- families with at least 2 linked reports: **36**
- families with at least 5 linked reports: **10**
- largest current family: **NCT02999178 (INBUILD), 17 linked reports**

The refreshed PubMed layer added registry-linked reports and three candidate families relative to v1. Examples of large or methodologically important families remain INBUILD, FIBRONEER-ILD/FIBRONEER-ON, admilparant/BMS-986278 trials, TETON-PPF, pirfenidone in unclassifiable progressive fibrosing ILD, RELIEF and observational PPF registries.

## Governance

- **No report is merged by this mapping step.**
- Registry entries, protocols, conference abstracts, primary articles, secondary analyses, letters and extensions remain separate reports.
- A family may contain reports that are later ineligible individually; family membership and eligibility are separate judgments.
- Mixed IPF/PPF programs remain intact until human report-level classification.
- DOI is not used as a family key.
- Final study/family identity is a human-confirmed G3 decision after selection.

## Reproduction

Script: `scripts/build_registry_family_map.py`

Required inputs:

- refreshed `publication_registry_mentions.csv` from GitHub Actions artifact `11812303667`;
- OpenAlex explicit supplementary candidates from the preserved OpenAlex artifact;
- formal citation-chasing candidates from the preserved citation-chasing artifact.

The identifier-level reconciliation and current counts are documented in `methods/CURRENT_SOURCE_RECONCILIATION_2026-10-13.md`.
