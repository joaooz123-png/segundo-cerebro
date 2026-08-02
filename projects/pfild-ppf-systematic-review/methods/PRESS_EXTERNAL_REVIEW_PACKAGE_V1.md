# External PRESS review package — PF-ILD / PPF PubMed strategy

Prepared: 2026-08-02  
Status: ready for independent information-specialist review; not externally approved

## 1. Review objective

Please peer-review the PubMed/MEDLINE search component of a systematic evidence census covering all retrievable literature directly concerning:

- progressive fibrosing interstitial lung disease (PF-ILD/PFILD);
- progressive fibrotic/fibrosing ILD phenotypes;
- progressive pulmonary fibrosis (PPF) in non-IPF fibrotic interstitial lung disease;
- historical terminology that describes the same or closely related disease-behaviour construct.

The primary product is an evidence map/census. Methodologically coherent systematic reviews will later be nested by question and design.

No language, date, age, human, publication-type or study-design restriction is applied at identification.

## 2. Candidate PubMed architecture

The PubMed candidate set uses two explicitly preserved strata rather than silently replacing the legacy retrieval.

### Stratum A — controlled candidate v2.2

File: `search/pubmed_v2_candidate.txt`

Characteristics:

- explicit singular/plural and hyphen variants;
- PF-ILD/PFILD acronyms;
- progressive fibrotic/fibrosing phenotype variants;
- PPF title terms and PPF title/abstract terms linked to ILD/non-IPF/fibrotic context;
- fibrotic/fibrosing ILD linked to progression terms;
- MeSH intersection for interstitial lung disease, pulmonary fibrosis and disease progression;
- field tags verified against recorded PubMed Query Translation.

Result: 2,629 unique PMIDs.

### Stratum B — legacy high-sensitivity safety net v1

The original v1 query and all 1,004 PMIDs are preserved in `data/project_state.json`.

This stratum is overbroad and contains generic uses of progressive pulmonary fibrosis, but it is retained because 138 records are not returned by v2.2 and some remain plausibly relevant after internal review.

### Exact PMID union

- v1: 1,004;
- v2.2: 2,629;
- overlap: 866;
- v1-only: 138;
- v2.2-only: 1,763;
- candidate union: 2,767 unique PMIDs.

Union files:

- `data/pubmed_v2_validation/pubmed_candidate_union_pmids.csv`
- `data/pubmed_v2_validation/pubmed_candidate_union_provenance.csv`
- `data/pubmed_v2_validation/pubmed_candidate_union_summary.json`

## 3. Sentinel validation

The sentinel set contains 62 PubMed-applicable known records spanning:

- foundational PF-ILD reviews and the 2018 European Respiratory Review series;
- INBUILD and related reports;
- pirfenidone trials;
- epidemiology, registries and claims studies;
- guidelines, consensus documents and correspondence;
- biomarkers, imaging and definitions;
- literature from the PF-ILD and PPF terminology periods.

Results:

- v1: 52/62;
- v2.2: 62/62;
- v2.2 apparent sentinel recall: 100%.

Files:

- `data/pubmed_v2_validation/pubmed_v2_sentinel_validation.csv`
- `data/seeds/seeds-01.json`
- `data/seeds/seeds-02.json`
- `data/seeds/seeds-03.json`

### Audited identifier correction

S029 had an incorrect PMID in the discovery seed:

- incorrect `32019572`: unrelated leflunomide/methotrexate toxicity case report;
- correct `31996266`: *Progression of fibrosing interstitial lung disease*;
- DOI confirmation: `10.1186/s12931-020-1296-3`.

The correction and reason are preserved in `data/metadata_corrections.csv`.

## 4. Query-translation audit

A v2.1 field-tag defect was detected internally:

- submitted: `"progressive pulmonary fibrosis"[Abstract]`;
- PubMed translated it to `All Fields`;
- corrected v2.2 uses `[Title/Abstract]` within the contextual block.

The v2.2 submitted query and actual PubMed Query Translation are stored in:

- `data/pubmed_v2_validation/pubmed_v2_validation.json`
- `data/pubmed_v2_validation/pubmed_v2_query.txt`

Please verify every field translation and identify any phrase-not-found, mapping or truncation concern.

## 5. Precision evidence

A deterministic random sample of 100 v2.2 records was enriched with titles and abstracts. Two deliberately different internal rule systems reviewed it:

1. sensitivity-first;
2. specificity/adversarial.

Consensus recommendations:

- retain for later human screening: 29;
- internal adjudication required: 35;
- candidate for later human exclusion: 36;
- exact agreement: 65%.

These are not eligibility decisions. The purpose is to expose noise mechanisms before PRESS review.

Files:

- `data/pubmed_v2_validation/precision_sample_dual_internal_review.csv`
- `data/pubmed_v2_validation/dual_internal_review_summary.json`
- `data/pubmed_v2_validation/pubmed_precision_audit_summary.json`

Main false-positive mechanisms observed:

- generic phrase “progressive pulmonary fibrosis” outside the modern PPF construct;
- IPF-only mechanistic and treatment studies;
- acute toxic or drug-induced fibrosis;
- post-infectious fibrosis;
- animal and in-vitro models;
- pulmonary vascular disease and other non-ILD contexts;
- incidental mentions of PPF approvals in broader reviews.

## 6. Legacy-only safety audit

All 138 v1-only records were enriched and reviewed internally. None were discarded from the union.

Consensus recommendations:

- retain for later human screening: 38;
- internal adjudication required: 54;
- candidate for later human exclusion: 46.

File: `data/pubmed_v2_validation/v1_only_safety_dual_internal_review.csv`

## 7. Requested PRESS assessment

Please assess and document:

1. Translation of the review objective into searchable concepts.
2. Boolean structure, nesting and redundancy.
3. Controlled vocabulary and missing MeSH concepts.
4. Free-text terms, spelling, plurals, acronyms and historical terminology.
5. Field tags and PubMed Query Translation.
6. Whether title-only PPF retrieval is justified.
7. Whether the progression-in-fibrotic-ILD block is too broad or too narrow.
8. Whether the three-MeSH intersection is useful or produces avoidable noise.
9. Whether the two-stratum architecture is defensible or should be replaced by one revised strategy.
10. Whether important terminology or sentinel categories are missing.
11. Whether the deterministic precision evidence indicates an unacceptable specificity problem.
12. How to translate the final strategy to Embase, CENTRAL, Scopus, Web of Science, CINAHL and LILACS.
13. Whether any limits or exclusions are justified at search stage. The current protocol prespecifies none.
14. Any reproducibility or reporting gap under PRISMA-S.

## 8. Requested verdict

Please choose one and provide line-level corrections:

- accept;
- accept with minor revisions;
- revise and resubmit;
- reject and reconstruct.

Any change to the retrieval strategy will generate a new version, new counts, new checksum and a documented protocol amendment. Previous versions will remain immutable.

## 9. Independence statement

The repository contains an internal adversarial reviewer agent and two deterministic internal review passes. These are quality-control aids only and are not represented as independent PRESS peer review. Formal Gate G1 approval remains pending until this package is reviewed by an independent qualified medical librarian or information specialist.