# External PRESS review package v2 — PF-ILD / PPF multibase search architecture

Prepared: 2026-09-04  
Status: ready for independent information-specialist review; not externally approved

## 1. Review objective

Please peer-review the identification strategy for a systematic evidence census / evidence map covering all retrievable literature directly concerning:

- progressive fibrosing interstitial lung disease (PF-ILD/PFILD);
- progressive fibrotic/fibrosing ILD phenotypes;
- progressive pulmonary fibrosis (PPF) in non-IPF fibrotic interstitial lung disease;
- historical terminology describing the same or closely related disease-behaviour construct.

Methodologically coherent systematic reviews will later be nested by question and study design. No language, publication date, age, human, publication-type or study-design restriction is applied at identification.

## 2. Search architecture

The search is intentionally organized as a high-recall multibase census rather than one efficacy-focused query. Four conceptual layers must be preserved across databases:

1. explicit PF-ILD/PFILD and progressive fibrosing/fibrotic ILD nomenclature;
2. the phrase `progressive pulmonary fibrosis`, protected by title-only retrieval or ILD/non-IPF/fibrotic context when searched more broadly;
3. progression terms combined with fibrosing/fibrotic ILD phrases;
4. controlled vocabulary for ILD, pulmonary/lung fibrosis and disease progression where the platform supports a thesaurus.

## 3. PubMed/MEDLINE reference strategy

Primary reference file: `search/pubmed_v2_candidate.txt`.

### Retrieval architecture

- controlled v2.2 stratum: 2,629 unique PMIDs;
- legacy v1 safety stratum: 1,004 unique PMIDs;
- overlap: 866;
- v2.2-only: 1,763;
- v1-only retained for safety: 138;
- candidate PubMed union: 2,767 unique PMIDs.

All 2,767 PMIDs were later enriched reproducibly:

- 2,761 complete EFetch records;
- 6 ESummary fallback records;
- 0 missing PMIDs;
- 2,496 with abstracts;
- 2,614 with DOI;
- 1,325 with PMCID.

The union remains a candidate identification set, not an eligible-study count.

## 4. Sentinel validation and known corrections

- PubMed-applicable sentinels: 62;
- v1 recovery: 52/62;
- v2.2 recovery: 62/62.

One apparent miss was a seed metadata error rather than a search failure:

- incorrect PMID `32019572`;
- corrected PMID `31996266`;
- correct report: *Progression of fibrosing interstitial lung disease*;
- DOI `10.1186/s12931-020-1296-3`.

The correction is preserved in `data/metadata_corrections.csv`.

## 5. PubMed query-translation audit

A v2.1 field-tag defect was identified because PubMed translated an `[Abstract]` phrase to All Fields. The v2.2 strategy uses `[Title/Abstract]` in the contextual PPF block. The submitted query and actual NCBI Query Translation are archived in `data/pubmed_v2_validation/`.

Please reassess all field tags, phrase behavior, automatic mapping and the justification for the title-only PPF component.

## 6. Precision and legacy-safety evidence

A deterministic 100-record v2.2 sample was reviewed internally by deliberately different sensitivity-first and adversarial rule systems:

- 29 retain for human screening;
- 35 internal adjudication required;
- 36 candidate human exclusions;
- exact internal agreement: 65%.

The 138 v1-only records were also retained and reviewed internally:

- 38 retain for human screening;
- 54 internal adjudication required;
- 46 candidate human exclusions.

No record was removed from the candidate union based on these internal reviews.

## 7. Platform-specific translations prepared for review

The following files are translations of the same conceptual architecture and have passed static internal safeguards, but have not yet been executed on the subscription platforms:

### Embase.com

File: `search/subscription/embase_com_v1.txt`

- title/abstract/keyword free text;
- Emtree explosion block;
- requires verification of preferred Emtree terms and Display full query on Embase.com.

### Scopus

File: `search/subscription/scopus_v1.txt`

- `TITLE-ABS-KEY` free text;
- `TITLE` protection for uncontextualized PPF phrase;
- optional proximity sensitivity line explicitly excluded from the frozen strategy until reviewed.

### Web of Science Core Collection

File: `search/subscription/web_of_science_v1.txt`

- `TS=` Topic fields;
- `TI=` title-only PPF component;
- optional NEAR sensitivity line excluded pending review.

### CINAHL on EBSCOhost

File: `search/subscription/cinahl_ebsco_v1.txt`

- TI/AB free-text blocks;
- provisional CINAHL Headings block;
- exact preferred heading names and explosion behavior must be verified on the institutional platform before execution.

### Cochrane CENTRAL

File: `search/subscription/central_v1.txt`

- `:ti,ab,kw` free-text blocks;
- MeSH descriptor intersection;
- execute through Cochrane Library Search Manager with CENTRAL as the target database.

Static validation CI passed all 5 translation files with zero missing conceptual layers and zero platform-marker failures. This is an engineering safeguard, not PRESS approval.

## 8. Regional-source limitation requiring assisted execution

SciELO Search and BVS/LILACS both returned HTTP 403 to GitHub-hosted runners in reproducible technical probes. This is treated as an access-path limitation and **must not** be reported as zero results.

Prepared query files:

- `search/manual_exports/lilacs_multilingual_query.txt`;
- `search/manual_exports/scielo_multilingual_query.txt`.

Execution protocol:

- `search/manual_exports/REGIONAL_EXPORT_PROTOCOL.md`.

Formal completion requires a normal-browser execution, displayed hit count, full RIS/CSV exports when offered, query/count evidence screenshot or PDF, date/time/timezone and SHA-256 checksums. LILACS must be restricted only by the database filter LILACS; no language/date/publication-type restriction is permitted.

Please assess the multilingual terminology and whether additional Portuguese/Spanish variants or DeCS terms should be added before browser execution.

## 9. Other already executed identification routes

The evidence census also includes complementary sources that should be evaluated for completeness and reporting rather than as substitutes for core bibliographic databases:

- Europe PMC: 1,125 candidate records retrieved; 53 lacked a matching PMID in the PubMed union;
- ClinicalTrials.gov: 146 initial NCT records;
- publication-to-registry mining: 68 unique NCT identifiers, including 56 additional NCT records recovered after the initial registry query;
- international registry supplementation through harmonized TrialCore/WHO ICTRP data;
- FDA/EMA regulatory documents;
- formal backward and forward citation chasing for all 62 PubMed-applicable sentinels through the Europe PMC REST API.

All raw/structured outputs are versioned and these routes create no automatic eligibility decisions.

## 10. Record/report/study-family safeguards

Please note the project intentionally distinguishes:

- **record**: one database result or registry entry;
- **report**: one publication, abstract, protocol, letter, correction, regulatory document, etc.;
- **study/family**: linked reports/registrations from the same underlying investigation or process.

DOI alone is prohibited as an automatic duplicate key because DOI collision/reuse among correspondence reports has already been observed. Preprints and journal publications remain distinct reports even when linked to one family.

## 11. Search execution manifest

File: `search/SEARCH_EXECUTION_MANIFEST.csv`.

For every source/platform, formal completion requires:

- database and platform;
- exact strategy file/version;
- local execution date/time/timezone;
- displayed hit count;
- exported record count;
- raw export file and format;
- SHA-256 checksum;
- search history or platform-generated parsed query where available;
- executor;
- PRESS status;
- notes on limits or anomalies.

Prepared translations are explicitly marked `prepared_not_executed`; regional blocked sources are `manual_export_required`.

## 12. Requested PRESS assessment

Please provide line-level comments addressing at least:

1. whether the review objective has been translated into appropriate searchable concepts;
2. omissions in terminology, acronyms, spelling, plural/hyphen variants and historical terminology;
3. PubMed Boolean structure, MeSH selection, field tags and PPF context protection;
4. whether the legacy safety-net stratum should remain as a separate identification stratum;
5. Embase Emtree terms and field syntax;
6. Scopus and Web of Science field/proximity choices;
7. exact CINAHL Headings and EBSCO syntax;
8. CENTRAL MeSH and Search Manager syntax;
9. multilingual LILACS/SciELO terms and possible DeCS additions;
10. whether any current search layer risks unacceptable false negatives;
11. whether any layer produces avoidable extreme noise without contributing recall;
12. completeness of trial-register, grey-literature, regulatory, conference and citation-search plans;
13. PRISMA-S reporting completeness;
14. any recommended search validation beyond the current 62-record sentinel set.

## 13. Requested verdict

For the overall identification strategy and each major bibliographic database, choose:

- accept;
- accept with minor revisions;
- revise and resubmit;
- reconstruct.

Any recommendation changing retrieval will create a new immutable search version, new execution count/checksum and an amendment log entry. Previous versions will remain preserved.

## 14. Independence statement

The repository contains internal adversarial agents, static CI validation and deterministic internal review passes. These are quality-control mechanisms only. Gate G1 remains formally pending until an independent qualified medical librarian or information specialist completes PRESS review. Human eligibility selection and final ROBIS/AMSTAR 2 audit are separate later stages.
