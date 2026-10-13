# G3 registry-linked publication-family map v1

Generated: 2026-10-13  
Status: internally derived candidate family map; human confirmation pending

## Purpose

Create reproducible **report → registry → study-family candidate** links without merging bibliographic reports.

Input layers:

1. PubMed union registry identifiers extracted from the 2,767 enriched records;
2. OpenAlex explicit supplementary candidates;
3. citation-chasing candidates outside and inside the PubMed union.

Only an **explicit registry identifier** creates a link in this layer. Title similarity alone is not used here.

## Current internally derived result

- candidate registry-linked families: **113**
- explicit report–registry links: **224**
- NCT families: **86**
- UMIN families: **9**
- EudraCT families: **5**
- jRCT families: **5**
- DRKS families: **4**
- ChiCTR families: **2**
- ISRCTN families: **2**
- families with at least 2 linked reports: **32**
- families with at least 5 linked reports: **10**
- largest current family: **NCT02999178 (INBUILD), 16 linked reports**

Examples of large or methodologically important candidate families include INBUILD, FIBRONEER-ILD/FIBRONEER-ON, admilparant/BMS-986278 trials, TETON-PPF, pirfenidone in unclassifiable progressive fibrosing ILD, RELIEF and observational PPF registries.

## Governance

- **No report is merged by this mapping step.**
- Registry entries, protocols, conference abstracts, primary articles, secondary analyses, letters and extensions remain separate reports.
- A family may contain reports that are later ineligible individually; family membership and eligibility are separate judgments.
- Mixed IPF/PPF programs remain intact until human report-level classification.
- DOI is not used as a family key.
- Final study/family identity is a human-confirmed G3 decision after selection.

## Reproduction

Script: `scripts/build_registry_family_map.py`

Required input environment variables:

- `PFILD_PUBLICATION_REGISTRY_MENTIONS`
- `PFILD_OPENALEX_EXPLICIT_CANDIDATES`
- `PFILD_CITATION_CANDIDATES`

The current source artifacts and checksums remain recorded in the project status/search manifest.
