# Protocol amendment log v2

This log is append-only after protocol v2 human approval. Never rewrite a historical entry; supersede it with a new entry.

## Status codes

- **PROPOSED:** drafted but not approved by named human guarantor.
- **APPROVED:** accepted before the affected review activity.
- **IMPLEMENTED:** change applied to workflow/data.
- **SUPERSEDED:** replaced by a later amendment without deleting history.
- **REJECTED:** considered but not adopted.

## Pre-freeze reconstruction

The following entries reconstruct major methodological decisions made before formal protocol-v2 freeze. They are disclosed to prevent a false impression of fully prospective planning.

### AMD-001 — Product architecture

- **Date:** 2026-08-02
- **Stage:** searches begun; human screening not begun
- **Status:** IMPLEMENTED; awaits named-author ratification
- **Original approach:** one broad “systematic review” of all document types.
- **Change:** define a systematic evidence census/evidence map as the umbrella product, with nested analytical systematic reviews for coherent questions.
- **Reason:** trials, cohorts, letters, guidelines, books, registries and regulatory documents cannot validly enter one undifferentiated synthesis.
- **Expected bias effect:** reduces inappropriate aggregation and selective post-hoc subgrouping.
- **Eligibility decisions already made:** none.

### AMD-002 — PubMed v1 not accepted as complete

- **Date:** 2026-08-02
- **Stage:** initial search imported; human screening not begun
- **Status:** IMPLEMENTED
- **Original approach:** 1,004-PMID PubMed retrieval treated as the formal base.
- **Change:** suspend completeness claim, validate against sentinels and create controlled v2.2 strategy while preserving v1 as a safety stratum.
- **Reason:** 10 of 62 PubMed-applicable sentinels were absent and the strategy produced both excessive noise and terminology gaps.
- **Expected bias effect:** increases sensitivity and transparency.
- **Eligibility decisions already made:** none.

### AMD-003 — Correct sentinel S029 identifier

- **Date:** 2026-08-02
- **Stage:** search validation; human screening not begun
- **Status:** IMPLEMENTED
- **Original value:** PMID 32019572.
- **Corrected value:** PMID 31996266.
- **Reason:** title/DOI verification showed the original PMID referred to an unrelated adverse-event case report.
- **Expected bias effect:** prevents false search-failure classification and incorrect record linkage.

### AMD-004 — Preserve v1 and v2.2 union

- **Date:** 2026-08-02
- **Stage:** strategy validation; human screening not begun
- **Status:** IMPLEMENTED
- **Change:** retain the 2,767-PMID union rather than replacing v1 with v2.2.
- **Reason:** 138 v1-only records required safety review before possible removal.
- **Expected bias effect:** favors sensitivity; increases screening burden.

### AMD-005 — Two independent human reviewers

- **Date:** 2026-08-02
- **Stage:** before human screening
- **Status:** APPROVED IN PRINCIPLE; personnel pending
- **Change:** require independent dual review for final eligibility and formal adjudication.
- **Reason:** reduce selection error and align with high-rigor conduct.

### AMD-006 — DOI-only merging prohibited

- **Date:** 2026-08-03
- **Stage:** deduplication development; human screening not begun
- **Status:** IMPLEMENTED
- **Change:** prohibit report merging on DOI alone.
- **Reason:** DOI 10.1056/NEJMc1917224 was linked to four distinct correspondence/reply records.
- **Expected bias effect:** prevents deletion of legitimate reports.

### AMD-007 — Preprints and publications remain separate reports

- **Date:** 2026-08-03
- **Stage:** family-linkage development; human screening not begun
- **Status:** IMPLEMENTED
- **Change:** connect preprint and journal article within a family but do not collapse them as duplicate reports.
- **Reason:** versions may differ in sample, outcomes, analyses and wording.

### AMD-008 — Expand registry search using publication identifiers

- **Date:** 2026-08-03
- **Stage:** source retrieval; human screening not begun
- **Status:** IMPLEMENTED
- **Change:** extract registry identifiers from publications and retrieve records absent from terminology-based registry searches.
- **Reason:** publication mining identified 56 additional NCTs, all recovered successfully.
- **Expected bias effect:** reduces registry-search terminology bias.

### AMD-009 — Invalidate first forward-citation run

- **Date:** 2026-08-03
- **Stage:** citation chasing; human screening not begun
- **Status:** IMPLEMENTED
- **Original result:** 2,634 backward edges and zero forward edges.
- **Change:** mark the run invalid and rerun after correcting parser control flow.
- **Reason:** an empty `referenceList` was returned before the parser checked the populated `citationList`.
- **Corrected result:** 2,634 backward and 7,078 forward edges; zero endpoint failures.
- **Expected bias effect:** prevents systematic loss of citing literature.

### AMD-010 — Regional sources require assisted export

- **Date:** 2026-08-03
- **Stage:** source-interface audit; human screening not begun
- **Status:** IMPLEMENTED AS ACCESS PLAN
- **Change:** classify SciELO and LILACS/BVS as not yet executed; require human-operated official RIS/CSV export.
- **Reason:** official search interfaces returned HTTP 403 to GitHub runners; SciELO ArticleMeta was confirmed to be a harvesting API without textual-search filtering.
- **Expected bias effect:** prevents falsely claiming an unexecuted regional search and avoids access-control circumvention.

### AMD-011 — Citation candidates kept outside formal identification counts

- **Date:** 2026-08-03
- **Stage:** citation chasing complete; human screening not begun
- **Status:** IMPLEMENTED
- **Change:** maintain 4,266 candidates outside the PubMed union in a separate discovery queue until reconciliation and formal import.
- **Reason:** citation-network membership alone does not establish target relevance or uniqueness.
- **Expected bias effect:** avoids inflated PRISMA identification counts and unreviewed additions.


### AMD-012 — OpenAlex supplementary identification layer

- **Date and timezone:** 2026-10-13 America/Sao_Paulo (formalization; source execution preceded formalization)
- **Proposer:** review automation team
- **Approving human(s):** pending named-author ratification
- **Status:** IMPLEMENTED; awaits named-author ratification
- **Review stage:** source identification; human screening not begun
- **Original wording/method:** OpenAlex not specified as a formal supplementary discovery layer.
- **Proposed wording/method:** preserve the 1,210 explicit-terminology OpenAlex candidates that remain after conservative existing-source matching as a supplementary identification layer; preserve the 4,713 broad-concept records as a sensitivity reservoir only.
- **Reason and evidence:** OpenAlex recovered conference/dissertation/preprint material not well represented by PubMed, including 1,061 explicit candidates without PMID.
- **Records or decisions already affected:** no eligibility decisions; no PRISMA counts changed automatically.
- **Expected direction/magnitude of bias:** improves sensitivity for grey/non-PubMed material while avoiding uncontrolled inflation by keeping the broad concept reservoir outside PRISMA identification.
- **Implementation commit/file:** search execution manifest; STATUS.md; OpenAlex workflow/artifact 11808957431.
- **Effect on registration/reporting:** report OpenAlex as supplementary; explicitly distinguish explicit candidate set from sensitivity reservoir.

### AMD-013 — Independent grey-source validation sentinels

- **Date and timezone:** 2026-10-13 America/Sao_Paulo
- **Proposer:** review automation team
- **Approving human(s):** pending named-author ratification
- **Status:** IMPLEMENTED; awaits named-author ratification
- **Review stage:** source validation; human screening not begun
- **Original wording/method:** ATS, ERS and BDTD strategies had no external-discovery sentinel set.
- **Proposed wording/method:** use 41 source-execution validation sentinels (15 ATS, 20 ERS, 6 BDTD), without assigning eligibility.
- **Reason and evidence:** source-specific searches require an independent sensitivity check before they can be considered complete.
- **Records or decisions already affected:** none; sentinels are validation records only.
- **Expected direction/magnitude of bias:** reduces false completeness claims and source-interface implementation error.
- **Implementation commit/file:** search/grey/GREY_SOURCE_SENTINELS_V1.csv and methods/GREY_SOURCE_SENTINELS_V1.md.
- **Effect on registration/reporting:** report sentinel validation as a search-quality control; any strategy change prompted by a miss requires a new amendment/version.

### AMD-014 — PRISMA-S search reporting and update policy

- **Date and timezone:** 2026-10-13 America/Sao_Paulo
- **Proposer:** review automation team
- **Approving human(s):** pending named-author ratification
- **Status:** PROPOSED / operationally prepared before human screening
- **Review stage:** search execution; human screening not begun
- **Original wording/method:** targeted contacts, final search-refresh timing, search-filter declaration and prior-strategy reuse were not explicit enough for complete PRISMA-S reporting.
- **Proposed wording/method:** adopt SEARCH_REPORTING_UPDATE_ADDENDUM_V1.md: targeted contact log, core-source refresh targeted within 3 months of manuscript submission, explicit declaration of no published methodological filters, and explicit declaration that no prior review strategy was substantively copied as the master search.
- **Reason and evidence:** PRISMA-S operational audit identified these as reportability gaps before selection.
- **Records or decisions already affected:** none.
- **Expected direction/magnitude of bias:** improves transparency and currency; targeted contact policy may reduce missing-study/data bias.
- **Implementation commit/file:** methods/PRISMA_S_AUDIT_V1.md and methods/SEARCH_REPORTING_UPDATE_ADDENDUM_V1.md.
- **Effect on registration/reporting:** add to protocol/OSF amendment history after named-author ratification.


## Post-freeze amendment template

Copy the following block for every proposed change.

```markdown
### AMD-XXX — Short title

- **Date and timezone:**
- **Proposer:**
- **Approving human(s):**
- **Status:** PROPOSED / APPROVED / IMPLEMENTED / SUPERSEDED / REJECTED
- **Review stage:**
- **Original wording/method:**
- **Proposed wording/method:**
- **Reason and evidence:**
- **Records or decisions already affected:**
- **Expected direction/magnitude of bias:**
- **Implementation commit/file:**
- **Effect on registration/reporting:**
```

## Amendment governance

- eligibility cannot be narrowed because retrieved evidence is inconvenient or heterogeneous;
- changes prompted by knowledge of study results require heightened justification and sensitivity analysis;
- corrections of factual identifiers are allowed but must remain logged;
- operational clarifications after a pilot must preserve the protocol’s substantive scope;
- any change after screening begins must state how prior records will be re-evaluated;
- registrations and manuscripts must report all material amendments.
