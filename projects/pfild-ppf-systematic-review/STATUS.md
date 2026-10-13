# PF-ILD / PPF project status

Snapshot: 2026-10-13

## Methodological target

Primary product: systematic evidence census / evidence map of PF-ILD and non-IPF PPF, with methodologically coherent nested systematic reviews by question and study design.

The project distinguishes **record**, **report**, and **study/family**. Automated agents may enrich, prioritize, propose duplicate/family links and audit methods, but may not silently finalize eligibility, deduplication, risk-of-bias judgments or synthesis conclusions.

## PubMed / MEDLINE

### Search architecture

- PubMed v1 legacy safety stratum: 1,004 unique PMIDs.
- PubMed v2.2 controlled stratum: 2,629 unique PMIDs.
- Overlap: 866.
- v1-only retained: 138.
- v2.2-only: 1,763.
- Candidate PubMed union: **2,767 unique PMIDs**.

### Sentinel validation

- PubMed-applicable sentinels: 62.
- v1 recovered: 52/62.
- v2.2 recovered: **62/62**.
- S029 incorrect PMID `32019572` was corrected to `31996266`; correction provenance is preserved in `data/metadata_corrections.csv`.

### Full enrichment

All 2,767 candidate PMIDs were enriched reproducibly through NCBI EFetch with ESummary fallback:

- complete EFetch: 2,761;
- ESummary fallback: 6;
- missing: 0;
- with abstract: 2,496;
- with DOI: 2,614;
- with PMCID: 1,325;
- PMID-order SHA-256: `6fa34a916379c89a33b1dfcd84d1a5f0ac28f059f57a7c45a454fb928e389111`.

GitHub Actions run `30785059672`, artifact `8844988389`, artifact digest `sha256:4c315e6f17f5cc099887fe0e43a91a24a2da8eba924a440e40b8cd94eea566f1`.

No PubMed candidate has been finally included or excluded by a human.

## Other executed identification sources

### Europe PMC

- 1,125 candidate records.
- 1,072 exact source-representation matches to PubMed by PMID.
- 53 records without a matching PMID in the PubMed candidate union.

### ClinicalTrials.gov and registry linkage

- initial ClinicalTrials.gov retrieval: 146 unique NCT records;
- registry mentions mined from PubMed metadata: 164;
- unique NCT identifiers mentioned: 68;
- already present in initial ClinicalTrials.gov set: 12;
- additional NCTs recovered from publication identifiers: **56/56**, 0 failures.

Additional non-US registry records and cross-registry family candidates are preserved separately.

### Regulatory sources

Core FDA and EMA documents relevant to PF-ILD/PPF treatment history have been captured as regulatory reports, not treated as primary studies.

### Citation chasing

Formal backward and forward citation chasing was executed for all 62 PubMed-applicable sentinel records through the Europe PMC REST API. Raw pages, checksums, edges, candidate records and overlap with the PubMed union are preserved.

### OpenAlex supplementary discovery

A reproducible OpenAlex Works search was executed as a supplementary sensitivity source:

- 7,299 unique OpenAlex works;
- 1,376 matched existing PubMed/Europe PMC records conservatively;
- 1,210 explicit supplementary candidates after existing-source matching;
- 1,061 of the explicit candidates have no PMID;
- explicit-candidate mix includes 543 articles, 428 conference abstracts, 42 conference papers, 27 dissertations, 22 preprints, 21 reviews and other report types;
- 62 explicit candidates are grey-literature-like records;
- a separate 4,713-record broad concept reservoir is preserved strictly for sensitivity auditing and is **not** treated as a PRISMA identification set.

OpenAlex is supplementary and does not replace Embase, Scopus, Web of Science, CINAHL or CENTRAL.

### BDTD theses and dissertations

The Brazilian BDTD/IBICT search has been executed partially:

- 129 unique record links discovered in the initial run;
- 126 records parsed;
- 55 theses and 71 dissertations;
- 2 high-priority exact-term candidates;
- 4 medium-priority conceptual candidates;
- 120 low-priority records retained for completeness;
- 3 detail-page failures;
- a later search stratum timed out.

A resilient collector revision now continues after isolated query failures rather than aborting subsequent strata. Until a complete rerun or manual recovery closes all query/detail gaps, BDTD remains **partial** and its 126 records must not be represented as an exhaustive thesis/dissertation search.

## Deduplication and report-family preparation

- 1,072 Europe PMC/PubMed source-representation duplicates linked by exact PMID.
- 42 Europe PMC–PubMed boundary candidate pairs.
- 25 of those are preprint → published-report family candidates.
- DOI alone is prohibited as an automatic merge key because reuse/collision among distinct correspondence reports has been observed.
- Preprint, protocol, article, letter, correction, registry entry and regulatory document remain distinct reports unless a human confirms the same source representation.

No final cross-source deduplication/family decision has been made by automation.

## Protocol and human-screening preparation

Protocol v2 is frozen before human eligibility selection and includes:

- formal evidence-census architecture;
- normative addendum;
- Portuguese independent-screening manual;
- append-only amendment log;
- OSF Generalized Systematic Review registration package;
- internal adversarial protocol review.

External OSF registration has not yet been claimed as submitted.

A deterministic blinded 120-record calibration pilot has been prepared for two independent human reviewers:

- 90 PubMed records from difficult strata;
- 10 Europe PMC non-PubMed records;
- 10 ClinicalTrials.gov records;
- 10 citation candidates outside the PubMed union.

Human eligibility decisions remain **0**.


## Supplementary discovery and saturation audit

### OpenAlex

A reproducible supplementary OpenAlex search completed successfully and was merged to `mainn` in PR #26.

- unique OpenAlex works retrieved: **7,299**;
- matched to existing PubMed/Europe PMC: **1,376**;
- explicit supplementary candidates not matched to the existing indexed corpus: **1,210**;
- explicit-phrase flag among those candidates: **989**;
- acronym-context flag: **418**;
- grey-like explicit candidates: **62**;
- broad concept-only sensitivity reservoir: **4,713**, preserved outside the PRISMA identification set pending yield audit;
- conference material within the explicit candidate set: **428 conference abstracts + 42 conference papers**;
- dissertations within the explicit candidate set: **27**.

OpenAlex is a supplementary discovery source only; it does not replace Embase, Scopus, Web of Science, CINAHL or CENTRAL.

### Independent academic-engine saturation checks

Independent discovery engines were used only as saturation controls, not as formal database substitutes. Full reconciliation is documented in `methods/SATURATION_AUDIT_2026-10-13.md`.

- Consensus: the top **10/10** PF-ILD/PPF results mapped to the 2,767-record PubMed union (one title differed only by subtitle/punctuation).
- SciSpace: four targeted semantic searches (definitions/criteria, epidemiology/prognosis, treatment, predictors/biomarkers) yielded **35 unique DOI-bearing papers** after cross-query de-duplication.
- Of those 35 SciSpace papers, **25** were already in PubMed and **8** additional papers were already among the OpenAlex explicit supplementary candidates.
- The remaining **2** were already captured by the formal sentinel citation-chasing workflow: PMID `36174209` (PPF criteria correspondence) and PMID `40786886` (broad antifibrotic systematic review/meta-analysis).

Thus, the expanded auxiliary audit produced **0 records outside the combined PubMed + OpenAlex explicit + formal citation-chasing discovery universe**. This supports saturation but does not prove exhaustiveness. It also confirms the value of citation chasing for title-oblique correspondence and broader evidence syntheses. Scite MCP and Elicit API could not be used because the connected accounts lack the required paid/API plans; this limitation is operational, not evidence of zero results.

## Regional sources: LILACS/BVS and SciELO

Technical probes demonstrated that both official search interfaces return HTTP 403 to GitHub-hosted runners. This is an access-path limitation and **must never be reported as zero results**.

Prepared files:

- `search/manual_exports/lilacs_multilingual_query.txt`;
- `search/manual_exports/scielo_multilingual_query.txt`;
- `search/manual_exports/REGIONAL_EXPORT_PROTOCOL.md`.

Formal completion requires normal-browser execution, displayed result totals, raw RIS/CSV export when offered, query/count evidence, timestamps and SHA-256 checksums. Until those exports are reconciled, these two sources remain pending.

## Subscription bibliographic databases

PRESS-ready, platform-specific translations have been prepared and statically validated for:

- Embase.com — `search/subscription/embase_com_v1.txt`;
- Scopus — `search/subscription/scopus_v1.txt`;
- Web of Science Core Collection — `search/subscription/web_of_science_v1.txt`;
- CINAHL on EBSCOhost — `search/subscription/cinahl_ebsco_v1.txt`;
- Cochrane CENTRAL — `search/subscription/central_v1.txt`.

Static CI validation passed 5/5 translation files. **Prepared does not mean executed.** These sources remain pending institutional platform access, exact hit counts, search-history evidence, raw exports and checksums.

Execution tracking: `search/SEARCH_EXECUTION_MANIFEST.csv`.

## PRESS

Internal PubMed validation is complete enough for external review, but formal Gate G1 approval remains pending independent PRESS review.

Current package: `methods/PRESS_EXTERNAL_REVIEW_PACKAGE_V2.md`, covering PubMed plus multibase translations and regional-source limitations.

Internal adversarial agents and CI checks are quality controls only and are not represented as independent PRESS peer review.

## Quality gates

| Gate | Domain | Current state |
|---|---|---|
| G0 | Architecture/protocol | Advanced; protocol v2 frozen before human selection; external registration/human guarantor steps remain |
| G1 | Search validity | Internally validated; independent PRESS review pending |
| G2 | Source coverage | Advanced partial: PubMed, Europe PMC, ClinicalTrials.gov, citation chasing, registry supplementation, regulatory sources and OpenAlex supplementary discovery executed; BDTD partially executed; LILACS/SciELO browser exports and subscription databases pending |
| G3 | Record management | Advanced preparation; exact duplicate layer and candidate families built; human boundary confirmation pending |
| G4 | Selection | Calibration pilot prepared; no human eligibility decisions yet |
| G5 | Full text | Not started formally |
| G6 | Extraction | Not started formally |
| G7 | Primary-study risk of bias | Not started |
| G8 | Synthesis | Not started |
| G9 | Certainty | Not started |
| G10 | Transparency/reproducibility | Advanced; searches, code, raw artifacts, amendments and checksums versioned |
| G11 | Final review audit | Not started; independent ROBIS/AMSTAR 2 audit reserved for final stage |

## Current blocking items before a maximum-quality claim

1. Independent PRESS review and resolution of recommendations.
2. Execution of Embase, Scopus, Web of Science, CINAHL and CENTRAL on their named platforms.
3. Browser-assisted LILACS and SciELO searches with raw exports and count evidence.
4. Complete BDTD recovery and execute ERS/ATS conference and remaining dissertation/grey-literature sources or document justified non-execution.
5. Two-reviewer human screening and adjudication.
6. Full-text retrieval and specific exclusion reasons.
7. Validated extraction, design-specific risk-of-bias assessment and appropriate synthesis.
8. GRADE/certainty assessment where applicable.
9. Independent final ROBIS/AMSTAR 2 audit.

No completed systematic-review or exhaustive-corpus claim is currently permitted.
