# Formal citation chasing of the PF-ILD/PPF sentinel set

## Valid execution

GitHub Actions run `30786461287` processed all 62 PubMed-applicable sentinel records through the official Europe PMC REST citation-network endpoints.

For each sentinel, the workflow requested:

- backward citation chasing: references cited by the sentinel;
- forward citation chasing: publications citing the sentinel.

Raw JSON responses, request URLs and SHA-256 digests are preserved in the workflow artifact.

## Results

- sentinels processed: 62
- endpoint requests/pages: 127
- edge-level citation links: 9,712
  - backward: 2,634
  - forward: 7,078
- unique candidate records: 5,184
  - already represented in the 2,767-PMID PubMed union: 918
  - outside the PubMed union: 4,266
- unique candidates by direction:
  - forward only: 3,774
  - backward only: 1,193
  - both directions: 217
- endpoint failures: 0

Candidate sources:

- MED/PubMed: 5,064
- Europe PMC preprints: 118
- unresolved source: 2

## Review-order prioritization

The 4,266 candidates outside the PubMed union were assigned non-decisional review priorities:

1. **P1 — direct terminology:** 2 records with canonical PF-ILD/PPF wording in the title.
2. **P2 — progression/ILD title:** 106 records combining progression terminology with fibrosis or ILD in the title.
3. **P3 — high network support:** 163 records linked by at least five sentinels or found in both directions.
4. **P4 — multiple sentinel links:** 914 records linked by two to four sentinels.
5. **P5 — broad recall:** 3,081 records linked by one sentinel.

The priority is only an order of human review. It is not an eligibility prediction, inclusion decision or exclusion decision.

## Direct-title records outside the PubMed union

- `PPR814707` — *Treatment patterns and patient journey in progressive pulmonary fibrosis: a cross-sectional survey* (2024), cited by five sentinels.
- `PPR882127` — *Prevalence of distress and changes over time among patients with progressive fibrosing interstitial lung disease* (2024), cited by three sentinels.

Both remain candidate preprints and require normal human screening and publication-family checks.

## Invalidated first run

Run `30786253606` is retained solely for audit. Its parser checked `referenceList` before `citationList` and returned the empty first structure, making forward citations appear to be zero. QA detected the contradiction in the raw files. The corrected parser was executed in run `30786461287`, and the workflow now fails unless both backward and forward counts are positive.

No result from the invalidated run may be used analytically.

## Reproducibility

Correct artifact:

- name: `pfild-sentinel-citation-chasing`
- run ID: `30786461287`
- artifact ID: `8845434002`
- digest: `sha256:da467d16e863b0ec8d2a79ffc099ed4558e8c9dee5fb1e0f8f04f7a05a1badb0`

The artifact contains:

- all 9,712 edge-level links;
- 5,184 deduplicated candidate records;
- per-sentinel coverage counts;
- raw response pages and manifest;
- an empty failures file;
- the machine-readable summary.

## Methodological effect

- human eligibility decisions created: 0
- PRISMA counts changed: 0

Candidates outside the current union enter a separate discovery queue. They must not be added to formal identification counts until source reconciliation, exact/near-duplicate checks and the protocol-defined import step are complete.
