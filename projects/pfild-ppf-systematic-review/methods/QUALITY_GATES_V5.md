# PF-ILD / PPF maximum-quality gates

Status date: 2026-08-02

## Target design

The primary product is a systematic evidence census / evidence map of all retrievable PF-ILD and non-IPF PPF literature. Methodologically coherent systematic reviews are nested within the map by question and study design.

PRISMA is a reporting guideline, not a quality seal. A maximum-quality claim requires all blocking gates below to pass.

| Gate | Domain | Pass criterion | Current state |
|---|---|---|---|
| G0 | Architecture and protocol | Questions, record-report-study units, nested syntheses, amendments and decision rules are fixed before selection | Partial — protocol consolidation pending |
| G1 | Search validity | Controlled vocabulary plus text words, all eligible sentinel references recovered, and independent PRESS review | Internally validated; external PRESS pending |
| G2 | Source coverage | Bibliographic databases, registers, grey literature, conferences, citation chasing and regulatory sources executed and archived | Failed — only PubMed candidate completed |
| G3 | Record management | Reproducible cross-source deduplication and report-to-study family linkage | Partial |
| G4 | Selection | Independent duplicate full-text eligibility decisions and prespecified adjudication | Not started |
| G5 | Full text | Lawful retrieval, non-retrieval logs and specific exclusion reasons | Not started |
| G6 | Extraction | Validated extraction forms and linked multiple reports | Not started |
| G7 | Primary-study risk of bias | Design-appropriate tools applied independently with reasons | Not started |
| G8 | Synthesis | Prespecified, question-specific synthesis without invalid pooling | Not started |
| G9 | Certainty | GRADE or another appropriate framework by outcome/question | Not started |
| G10 | Transparency | Protocol, searches, exports, code, decisions and derived data versioned | Advanced partial |
| G11 | Final review audit | Low ROBIS risk and no critical AMSTAR 2 weakness where applicable | Not started |

## Gate G1 internal evidence

### Sentinel validation

- PubMed-applicable sentinels: 62.
- PubMed v1 recovered: 52/62 (83.9%).
- PubMed v2.2 recovered: 62/62 (100%).
- One apparent v2.1 failure was caused by an incorrect seed identifier rather than a search failure:
  - S029 old PMID: `32019572` — unrelated drug-toxicity case report.
  - S029 corrected PMID: `31996266` — *Progression of fibrosing interstitial lung disease*.
  - The correction is preserved in `data/metadata_corrections.csv`.

### Query-translation audit

The v2.1 use of `[Abstract]` was translated by PubMed to `All Fields`. It was corrected in v2.2 to `[Title/Abstract]`. The final recorded Query Translation preserves the intended field restriction.

### Candidate PubMed identification architecture

The project does not discard the broader v1 retrieval merely because v2.2 has better syntax and sentinel recall. The candidate PubMed set is a two-stratum union:

1. **Controlled stratum:** PubMed v2.2 — 2,629 unique PMIDs.
2. **Legacy safety-net stratum:** PubMed v1 — 1,004 unique PMIDs.
3. **Overlap:** 866 PMIDs.
4. **v2.2-only:** 1,763 PMIDs.
5. **v1-only:** 138 PMIDs.
6. **Candidate union:** 2,767 unique PMIDs.

All 138 v1-only records remain in the candidate union. Internal reviews are prioritisation aids only:

- 38 retained by both internal reviewers for human screening;
- 54 require internal adjudication;
- 46 are candidates for later human exclusion;
- zero eligibility or PRISMA decisions were made.

### Precision audit

A deterministic random sample of 100 v2.2 records was enriched with PubMed title/abstract metadata and reviewed by two intentionally different internal rule systems:

- sensitivity-first reviewer;
- specificity/adversarial reviewer.

Consensus:

- 29 retain for human screening;
- 35 internal adjudication required;
- 36 candidate human exclusions;
- exact internal agreement: 65%.

This indicates a deliberately sensitive search with substantial screening burden. It is not a reason to remove records automatically.

## Gate G1 verdict

**Internal verdict: acceptable for submission to external PRESS review, but not formally passed.**

Formal approval still requires an independent qualified information specialist to review the strategy, translations, sentinel set, database adaptation plan and precision evidence. Any external recommendations must be logged and trigger a new immutable search version if they change retrieval.

## Independent requirements

The project cannot self-certify the following:

1. PRESS peer review by an independent medical librarian or information specialist.
2. Independent duplicate final eligibility decisions.
3. Independent final ROBIS / AMSTAR 2 audit where applicable.

## Core standards

- PRISMA 2020: https://www.prisma-statement.org/prisma-2020
- PRISMA-S: https://www.prisma-statement.org/prisma-search
- PRISMA-P: https://www.prisma-statement.org/protocols
- PRISMA-ScR: https://www.prisma-statement.org/scoping
- Cochrane Handbook Chapter 4: https://training.cochrane.org/handbook/current/chapter-04
- ROBIS: https://www.bristol.ac.uk/population-health-sciences/projects/robis/
- AMSTAR 2: https://amstar.ca/Amstar-2.php