# PF-ILD / PPF agent operating rules

These rules apply to every AI agent working inside this directory.

## Scientific objective

Build a reproducible census of all indexed and retrievable literature directly concerning PF-ILD and its conceptual continuation as PPF in non-IPF fibrotic interstitial lung disease. Do not narrow the corpus in advance by disease, treatment, biomarker, outcome, study design, language, country, date, or publication type.

## Units of evidence

Maintain three separate entities:

1. **Record** — one database result or registry entry.
2. **Report** — one publication, abstract, chapter, protocol, correction, letter, or regulatory document.
3. **Study/family** — all reports and registrations arising from the same underlying study, trial, registry, cohort, guideline process, or correspondence chain.

A report may be linked to a study family without being a duplicate.

## Required provenance

Every change must preserve:

- source and platform;
- exact query or discovery route;
- search or verification date;
- stable identifiers;
- original value;
- corrected/enriched value;
- reason and evidence for the change;
- agent recommendation and human decision as separate fields.

## Human-review boundary

Agents may recommend, prioritize, flag, enrich, or audit. They must not silently finalize eligibility, deduplication, family linkage, risk-of-bias judgments, or synthesis conclusions.

## Vancouver

Keep all authors in source data. For a rendered reference, use the first six authors followed by `et al.` when there are more than six, unless the selected journal requires another variant. Verify journal abbreviation, year, volume, issue, pages/e-location, and DOI against an authoritative source.

## Access

Do not bypass paywalls. Track legal full-text routes: publisher open access, PubMed Central, Europe PMC, institutional repository, accepted manuscript, preprint, library access, interlibrary loan, or author request.

## Current baseline

Read `STATUS.md` and `data/project_state.json` before work. The baseline dated 2026-08-02 contains 1,004 unique PubMed PMIDs, 66 discovery seeds, zero screened records, and zero included reports.
