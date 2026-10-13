# Current-source reconciliation — 2026-10-13

Status: deterministic identifier-level reconciliation after the formal PubMed update and sequential G2/G3 refresh. No eligibility decision, PRISMA count, or human duplicate/family judgment is created here.

## Current indexed core

- PubMed candidate union: **2,855 unique PMIDs**.
- Europe PMC: **1,192 records**.
- Exact Europe PMC → PubMed source-representation matches by PMID: **1,129**.
- Europe PMC records without matching PMID in the current PubMed union: **63**.

## OpenAlex explicit supplementary candidates

The OpenAlex search itself is preserved as executed: **1,210 explicit supplementary candidates** were identified after comparison with the earlier indexed universe.

Reconciliation against the refreshed 2026-10-13 PubMed + Europe PMC identifiers found:

- **58/1,210** now match the refreshed indexed core by PMID and/or normalized DOI;
- **1,152/1,210** remain unmatched to the current PubMed/Europe PMC indexed core.

This is an overlap update only. The OpenAlex execution count is not rewritten retrospectively.

## Citation-chasing candidates

The formal sentinel citation-chasing run remains **5,184 unique candidates**.

After comparison with the refreshed 2,855-PMID union by PMID and/or normalized DOI:

- **919/5,184** now match the current PubMed union;
- **4,265/5,184** remain outside the current PubMed union.

The prior August value of 4,266 outside PubMed is retained as the historical run-time comparison; the current reconciliation is 4,265.

## Registry-linked candidate study families

The registry-family derivation was rerun locally with:

1. the refreshed **176** PubMed publication-registry mentions;
2. the original OpenAlex explicit candidate set;
3. the original formal citation-chasing candidate set.

Current deterministic output:

- candidate registry-linked families: **116**;
- explicit report–registry links: **236**;
- NCT families: **87**;
- UMIN families: **10**;
- EudraCT families: **5**;
- jRCT families: **5**;
- DRKS families: **4**;
- ChiCTR families: **3**;
- ISRCTN families: **2**;
- families with >=2 linked reports: **36**;
- families with >=5 linked reports: **10**;
- largest current family: **NCT02999178 (INBUILD), 17 linked reports**.

## Governance

- DOI/PMID matching above is used only for conservative cross-source overlap accounting.
- No bibliographic report is merged solely by DOI.
- Preprints, protocols, abstracts, primary articles, secondary analyses, letters, registry entries and regulatory documents remain distinct reports.
- Registry-family membership and report eligibility remain separate human judgments.
- Current reconciliation values should be used for operational queues; historical search execution values remain unchanged in the execution manifest.
