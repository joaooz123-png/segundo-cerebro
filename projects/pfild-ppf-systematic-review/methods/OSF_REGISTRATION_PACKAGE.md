# OSF registration package — PF-ILD / PPF evidence census

This document maps protocol v2 to the OSF **Generalized Systematic Review** registration. It is a preparation package, not proof that registration has been submitted.

## 1. Proposed title

**Progressive fibrosing interstitial lung disease and progressive pulmonary fibrosis: a systematic evidence census, evidence map and platform for nested systematic reviews**

## 2. Review type

- systematic evidence census;
- scoping/evidence-map review;
- platform for nested systematic reviews and meta-analyses.

## 3. Current stage at registration

### Completed before registration

- terminology development and search testing;
- searches in PubMed, Europe PMC, ClinicalTrials.gov and selected open sources;
- metadata enrichment and technical deduplication;
- citation chasing from 62 sentinel references;
- development of automated non-decisional prioritization and family-linkage tools.

### Not begun before registration

- human title/abstract screening;
- human full-text eligibility assessment;
- final inclusion/exclusion;
- analytical data extraction;
- risk-of-bias assessment;
- evidence synthesis or meta-analysis;
- certainty assessment.

**Required disclosure:** the registration is prospective for human selection and analysis but not for initial search development or retrieval.

## 4. Research question

What is the extent, nature, chronology, terminology, methodological composition and study-family structure of literature directly addressing PF-ILD/PPF or an equivalent progressive fibrotic non-IPF ILD phenotype, and what analytically coherent evidence exists for definitions, burden, prognosis, diagnosis/monitoring and interventions?

## 5. Background and rationale

PF-ILD and PPF describe progression across heterogeneous fibrosing ILDs other than IPF. Terminology, definitions and eligible etiologies have changed over time. Evidence is distributed across trials, observational cohorts, guidelines, reviews, registries, conference abstracts, preprints, regulatory records and other document types. A conventional intervention-only review cannot adequately map this full literature, while a broad census without nested analytical structure cannot support effect estimates. The project therefore separates evidence mapping from domain-specific systematic synthesis.

## 6. Primary objective

Create a reproducible census and evidence map of direct PF-ILD/PPF evidence at record, report and study-family levels.

## 7. Secondary objectives

- map terminology and progression criteria;
- classify evidence by ILD etiology, design, document role and domain;
- identify ongoing, unpublished and duplicate/family-related evidence;
- identify evidence gaps;
- define coherent subsets for nested systematic reviews;
- support continuous updates without overwriting historical versions.

## 8. Eligibility criteria

Use the complete criteria in `PROTOCOL_V2.md`. Summary:

### Include in direct layer

Reports in which PF-ILD/PPF or an explicitly equivalent progressive fibrotic non-IPF ILD phenotype is central, measured, defined, treated, predicted, registered or reported, including documents linked to eligible study families.

### Include in contextual layer

Reports necessary to interpret the construct’s definition, history, measurement, IPF-to-PPF methodological transfer or regulatory boundaries, with explicit justification.

### Exclude

Unrelated meanings of PPF; pulmonary fibrosis without relevant ILD progression; IPF-only reports without material connection; incidental mentions; non-human reports outside the explicit mechanistic module; non-evidentiary web material; and exact duplicate source representations.

### Restrictions

No limits by date, language, geography, publication status or document type.

## 9. Information sources

Planned sources are listed in `PROTOCOL_V2.md` and the source matrix. They include bibliographic databases, regional databases, trial registries, preprint sources, theses, conference sources, regulatory sources and citation chasing.

At registration, clearly distinguish:

- sources formally executed with raw exports;
- sources technically probed but not executed;
- sources pending subscription or assisted export.

## 10. Search strategy

The complete PubMed strategy and NCBI Query Translation are preserved in the repository and form the PRESS-review base. Other searches will be translated by concept and platform syntax. No date, language or design filters will be used in the census search.

A verified sentinel set is used for search validation. Automated searching must preserve exact queries, execution dates, raw files, result counts and checksums.

## 11. Data management

The project distinguishes retrieval units, bibliographic records, reports and studies/families. Exact duplicates may be consolidated with provenance. Different reports from the same study remain separate and are family-linked.

Data, scripts, strategies and amendments are versioned in GitHub. Large raw artifacts are preserved through immutable or time-limited workflow artifacts and should be migrated to durable repository storage before publication.

## 12. Selection process

Two reviewers will independently screen titles/abstracts and full texts. Disagreement will be resolved by consensus or third-party adjudication. Automated tools may prioritize or flag records but cannot make final decisions.

A stratified pilot of at least 100 records will precede production screening. Pilot results and any operational clarification will be logged.

## 13. Data extraction/charting

Census-level fields are specified in protocol v2. Domain-specific analytical forms will be frozen before outcome extraction. One reviewer will extract and a second verify, or critical fields will be independently duplicated.

## 14. Risk of bias

Risk of bias is not a census-level exclusion rule. Design-specific tools will be used within analytical questions, including RoB 2, ROBINS-I, QUIPS, an appropriate diagnostic-accuracy tool, and appropriate JBI/CASP instruments. ROBIS will be used for review-level evidence and final review audit as applicable.

## 15. Outcomes and variables

The evidence census maps domains rather than using outcomes as eligibility criteria. Potential analytical outcomes include:

- mortality and transplant-free survival;
- FVC change and categorical decline;
- DLCO change;
- acute exacerbation and hospitalization;
- progression-free survival or composite progression;
- symptoms, exercise capacity and quality of life;
- treatment discontinuation and adverse events;
- resource use and costs;
- diagnostic/prognostic performance.

Each nested review will specify a limited set of critical and important outcomes before extraction.

## 16. Synthesis

The umbrella output will use descriptive counts, timelines, evidence matrices, maps and family networks. Meta-analysis will be restricted to coherent nested questions. SWiM principles will guide structured synthesis without meta-analysis. Statistical-significance vote counting will not be used.

## 17. Certainty

GRADE will be applied to appropriate effect estimates. GRADE-CERQual may be used for qualitative synthesis. No single certainty rating will be assigned to the heterogeneous census.

## 18. Publication-bias and missing-evidence assessment

Registry, protocol, abstract, preprint and publication links will be compared. Funnel-plot or statistical small-study-effect methods will be used only when assumptions and study counts support them.

## 19. Amendments

All changes after protocol freeze will be logged with stage, reason, effect and approving humans. Search updates will create new frozen versions and will not overwrite prior PRISMA data.

## 20. Contributors to be named before submission

- guarantor and corresponding author;
- clinical lead;
- information specialist/PRESS reviewer;
- two screeners;
- adjudicator;
- statistical/methodological lead;
- risk-of-bias reviewers;
- patient/public contributor, if recruited.

## 21. Conflicts of interest and funding

To be completed by each named contributor. Relationships with manufacturers of antifibrotic or immunomodulatory therapies must be disclosed. Tool providers and AI systems do not qualify as authors but their roles should be transparently described.

## 22. Data availability

The planned public package includes:

- protocol and amendments;
- complete search strategies;
- source and export log;
- deduplication/family rules;
- eligibility-decision dataset where licensing permits;
- exclusion reasons;
- extraction forms and derived data;
- analysis code;
- PRISMA flow and checklists.

Raw licensed database exports may be archived privately or shared only where permitted.

## 23. Registration actions

1. Approve protocol v2 with named human authors.
2. Assign contributor roles and declarations.
3. Create or identify the OSF project.
4. Upload protocol, search package, amendment log and current status statement.
5. Submit a read-only Generalized Systematic Review registration.
6. Record the OSF DOI/URL and timestamp in the repository.
7. Register each eligible nested analytical review in PROSPERO before its domain-specific selection/extraction, where feasible.
