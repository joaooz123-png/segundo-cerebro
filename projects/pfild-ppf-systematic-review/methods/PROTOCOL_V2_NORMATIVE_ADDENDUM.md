# Protocol v2 normative addendum

This addendum is part of protocol v2 and resolves operational ambiguities identified during internal adversarial review. If wording conflicts, this addendum governs until protocol v2 is consolidated into a later approved version.

## A1. Separation of evidence roles

Every included report must receive one role:

- `PRIMARY-HUMAN` — original human data relevant to the target construct;
- `SECONDARY-REVIEW` — systematic, scoping or narrative review;
- `GUIDELINE-CONSENSUS` — guideline, statement or consensus;
- `PROTOCOL-REGISTRY` — protocol or registry record;
- `CONFERENCE` — abstract, poster or proceedings report;
- `PREPRINT` — non-peer-reviewed manuscript;
- `COMMENTARY` — editorial, letter, reply or perspective;
- `CORRECTION` — correction, erratum or retraction notice;
- `REGULATORY-HTA` — regulatory or health-technology-assessment report;
- `THESIS-BOOK` — thesis, dissertation, book or chapter;
- `QUALITATIVE-ECONOMIC` — qualitative, mixed-methods, resource-use or economic report;
- `MECHANISTIC` — non-human or translational contextual report.

Secondary reviews, guidelines and opinion reports must not be treated as primary effect evidence. They may support mapping, citation discovery, definitions and contextual synthesis.

## A2. Case reports and small case series

Case reports and case series are eligible for the census when PF-ILD/PPF is central, including unusual etiologies, treatment experiences, adverse events or diagnostic challenges. They will be clearly tagged and excluded from comparative effect estimates unless a domain-specific method explicitly supports their use.

## A3. Contextual-layer control

Contextual inclusion requires all three:

1. a named contextual category from the screening manual;
2. a one-sentence material-link justification;
3. identification of the direct report, criterion, method, trial, guideline or regulatory question that the contextual report helps interpret.

A report cannot enter the contextual layer solely because it is frequently cited, historically important in ILD generally or clinically interesting.

Contextual-layer usage will be audited. If more than 20% of full-text inclusions are contextual, a blinded sample will be reviewed for scope creep before screening continues.

## A4. Mechanistic module boundary

Completeness claims for the core human evidence census do not extend automatically to all pulmonary-fibrosis animal or molecular literature.

Mechanistic records may enter the contextual module when found by the core searches and explicitly linked to PF-ILD/PPF. A comprehensive mechanistic review would require a separately frozen search and protocol. The absence of such a separate search must be disclosed.

## A5. Citation-chasing plan

Citation chasing occurs in stages:

1. **Development stage:** backward and forward chasing of the verified sentinel set, already performed.
2. **Eligibility stage:** backward chasing of all included systematic reviews, guidelines and key primary reports.
3. **Family-completion stage:** targeted forward/backward chasing for study families with missing protocols, registry results, abstracts or secondary reports.
4. **Saturation stage:** one additional citation-search cycle for newly included direct reports that were not identified by database searching.

Citation chasing will stop when a complete cycle yields no new direct-layer eligible report, or when a documented source limitation prevents continuation. Counts by cycle will be retained.

Candidates from citation chasing remain outside formal identification counts until they are normalized, deduplicated and imported with source provenance.

## A6. Search-date and update rule

The final report must state the last search date for every source. Before manuscript submission, sources that can materially change will be updated when the oldest main-database search is more than six months old, unless a shorter interval is required by journal or review context.

The update will use the frozen strategy or a logged amendment and will create a separate update PRISMA segment.

## A7. Language handling

No language restriction applies.

- machine translation may support title/abstract triage;
- final exclusion based on nuanced content must be verified by a competent human reader, professional translation or a documented high-confidence translation process;
- translated quotations will be checked against the original;
- inability to obtain adequate translation will be reported as an unresolved limitation, not silently excluded.

## A8. Retractions, corrections and expressions of concern

Before synthesis, included reports will be checked for:

- retraction;
- expression of concern;
- correction or erratum;
- duplicate publication;
- material post-publication amendment.

Retraction notices and corrections are retained as family reports. Retracted evidence will not support clinical conclusions and its prior influence will be documented.

## A9. Study-family outcome hierarchy

When multiple reports present overlapping data, the study family remains one underlying study for participant counting and effect estimation.

For each outcome/time point, select the most informative source using this hierarchy, subject to verification:

1. final peer-reviewed report with the most complete eligible population and longest prespecified follow-up;
2. supplementary appendix or verified regulatory report providing additional valid detail;
3. earlier peer-reviewed report for outcomes not reported later;
4. preprint or conference abstract when no fuller report exists, with status noted;
5. registry results when publication data are unavailable or to assess discrepancies.

Data from multiple reports may be combined only when they are demonstrably non-overlapping or complementary. Conflicts must be recorded and resolved without choosing the more favorable result merely because of direction or significance.

## A10. Overlapping observational cohorts

Potentially overlapping cohorts will be compared by centres, dates, sample size, eligibility, authors and baseline characteristics.

For the same analysis question:

- use the most complete non-duplicative cohort;
- retain other reports for complementary outcomes or time points;
- perform sensitivity analyses where overlap remains uncertain;
- never sum overlapping participants as independent observations.

## A11. PRISMA accounting for layers

The PRISMA flow will report:

- records/reports entering direct evidence;
- reports entering contextual evidence;
- reports excluded at full text with reasons;
- studies/families represented by direct reports.

Contextual reports will not inflate the count of direct studies. Record, report and study counts must be labelled explicitly.

## A12. Pilot and production screening governance

The pilot sample must include:

- direct P1 and broad P5 records;
- modern and historical terminology;
- IPF-only and mixed IPF/PPF records;
- records without abstracts;
- etiologic progression studies without PPF wording;
- preprints, protocols, conference abstracts and correspondence;
- contextual candidates;
- mechanistic false positives;
- suspected family/duplicate cases.

No reviewer may see the other reviewer’s decision before submitting their own where the platform supports blinding.

After every 500 records, a drift check will compare exclusion reasons and direct/contextual proportions between reviewers. Material drift triggers recalibration and re-review of an appropriate sample.

## A13. Full-text exclusion hierarchy

Assign one primary exclusion reason using the first applicable item:

1. wrong construct/PPF meaning;
2. wrong disease — no relevant fibrosing ILD;
3. wrong phenotype — no material progression construct;
4. IPF-only without material bridge;
5. wrong evidence layer — non-human and not eligible mechanistic context;
6. target data not separable and document not otherwise map-eligible;
7. incidental mention only;
8. non-evidentiary material;
9. exact duplicate source representation;
10. report cannot be identified or obtained sufficiently for judgment;
11. other, with mandatory explanation.

Document type, absence of desired outcomes and perceived quality are not exclusion reasons for the census.

## A14. Appraisal of reviews and guidelines

When reviews or guidelines are analyzed as evidence products:

- systematic reviews will undergo ROBIS and/or AMSTAR 2 as appropriate;
- guidelines may be assessed with AGREE II or a justified current equivalent;
- narrative reviews and commentaries will not receive quantitative risk-of-bias ratings intended for primary studies but will be labelled by evidence role and sourcing method.

Their conclusions will not substitute for independent assessment of eligible primary studies.

## A15. AI governance

For every substantial machine-generated dataset, preserve:

- model/tool name and version when available;
- prompt or rule set;
- date;
- input dataset checksum;
- output checksum;
- human-review status;
- known limitations and invalidated runs.

AI labels are auxiliary metadata. They must not overwrite raw source fields or human decisions.

## A16. Minimum conditions before human production screening

Production screening may begin only after:

- protocol v2 and this addendum are approved by the named guarantor;
- reviewer roles are assigned;
- screening manual is approved;
- the pilot dataset is frozen;
- conflict and adjudication procedures are configured;
- the machine-priority fields are visually separated from human-decision fields;
- a backup/export method for decisions is verified.

Completion of every database search is not required before a pilot, but production screening should use a clearly versioned dataset, and later imports must be handled as documented update batches.
