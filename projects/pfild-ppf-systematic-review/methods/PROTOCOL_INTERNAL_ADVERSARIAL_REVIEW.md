# Internal adversarial review of protocol v2

**Review type:** internal second-pass methodological challenge  
**Independence status:** not an external peer review and not a substitute for PRESS, ROBIS or journal peer review  
**Review date:** 2026-08-03  

## Overall judgment

Protocol v2 is sufficiently structured to freeze core scope before human screening, provided that the normative addendum is treated as part of the protocol. It is not yet externally registered, PRESS-reviewed or approved by named human contributors.

## Review questions

The adversarial pass asked whether the protocol could:

- permit post-hoc inclusion of almost any ILD article;
- confuse broad evidence mapping with causal/clinical synthesis;
- double-count participants across reports;
- remove reports through unsafe deduplication;
- overuse an undefined contextual layer;
- falsely claim comprehensive mechanistic or regional coverage;
- allow AI labels to become eligibility decisions;
- obscure searches conducted before registration;
- produce inflated PRISMA counts from citation-network candidates;
- handle historical terminology and mixed IPF/PPF populations consistently.

## Findings and resolutions

### F1 — Umbrella scope could be mistaken for one analytical review

- **Severity:** critical if unresolved
- **Finding:** heterogeneous documents cannot enter one pooled or unified quality judgment.
- **Resolution:** protocol defines the evidence census as primary and requires separately frozen nested reviews.
- **Status:** resolved.

### F2 — Contextual layer could become an unlimited catch-all

- **Severity:** high
- **Finding:** “important context” is inherently subjective and could inflate the corpus.
- **Resolution:** addendum requires a category, one-sentence material-link justification and a named target report/method/question. It triggers audit if contextual reports exceed 20% of full-text inclusions.
- **Status:** resolved operationally; requires human audit.

### F3 — Historical studies could be unfairly excluded by modern PPF criteria

- **Severity:** high
- **Finding:** requiring 2022 criteria would introduce temporal bias.
- **Resolution:** protocol defines terminology eras and accepts substantively equivalent historical progression phenotypes.
- **Status:** resolved.

### F4 — IPF bridge could allow uncontrolled IPF expansion

- **Severity:** high
- **Finding:** much of pulmonary-fibrosis literature concerns IPF and could overwhelm the target corpus.
- **Resolution:** IPF-only reports require an explicit material transfer to PF-ILD/PPF and contextual categorization; generic similarity is insufficient.
- **Status:** resolved operationally; pilot must stress-test this rule.

### F5 — Mechanistic scope was potentially unbounded

- **Severity:** high
- **Finding:** “all mechanistic literature” would require a separate search universe.
- **Resolution:** addendum states that completeness claims do not extend to all animal/molecular fibrosis evidence; a comprehensive mechanistic module requires a separate protocol/search.
- **Status:** resolved.

### F6 — Document inclusion could be confused with evidence weight

- **Severity:** high
- **Finding:** letters, reviews, guidelines and regulatory reports have different evidentiary roles.
- **Resolution:** mandatory evidence-role classification; non-primary reports cannot substitute for primary effect evidence.
- **Status:** resolved.

### F7 — Family linkage lacked a prespecified outcome hierarchy

- **Severity:** critical for meta-analysis
- **Finding:** multiple reports may lead to duplicate participants or selective selection of favorable estimates.
- **Resolution:** addendum specifies family-level outcome-source hierarchy and overlapping-cohort rules.
- **Status:** resolved for planning; must be implemented in extraction forms.

### F8 — DOI could delete distinct correspondence

- **Severity:** critical
- **Finding:** one DOI was shared by four distinct records.
- **Resolution:** DOI-only merging prohibited; identifier, title, authorship, role and context required.
- **Status:** resolved and regression-tested.

### F9 — Citation chasing could inflate identification counts

- **Severity:** high
- **Finding:** network membership is not evidence of relevance or uniqueness.
- **Resolution:** 4,266 external candidates remain in a separate queue until normalized, deduplicated and formally imported.
- **Status:** resolved.

### F10 — Citation chasing was only sentinel-based

- **Severity:** moderate/high
- **Finding:** sentinel chasing alone cannot prove saturation.
- **Resolution:** addendum requires later chasing of included reviews/guidelines/key studies, family completion and a final saturation cycle.
- **Status:** planned, not completed.

### F11 — First forward-citation output passed superficial workflow checks

- **Severity:** critical process failure
- **Finding:** forward count was zero because of parser control flow, while the raw response held citation data.
- **Resolution:** invalidated run preserved; parser corrected; CI now requires positive results in both directions; corrected run produced 7,078 forward edges.
- **Status:** resolved with regression invariant.

### F12 — Regional-source probes could be misreported as searches

- **Severity:** high
- **Finding:** technical access testing is not a bibliographic search.
- **Resolution:** SciELO/LILACS remain explicitly unexecuted; exact assisted-export protocol created.
- **Status:** resolved in reporting; exports pending.

### F13 — Protocol timing could be described misleadingly

- **Severity:** critical for trust
- **Finding:** search development preceded protocol v2.
- **Resolution:** protocol and OSF package explicitly distinguish completed technical/search work from not-yet-started human screening and analysis.
- **Status:** resolved.

### F14 — Language inclusion lacked a verification pathway

- **Severity:** moderate
- **Finding:** “no language restriction” is insufficient without a translation method.
- **Resolution:** addendum permits machine-assisted triage but requires competent verification for nuanced final exclusions.
- **Status:** resolved in method; resources pending.

### F15 — Retractions and corrections were not an explicit final check

- **Severity:** moderate/high
- **Finding:** retracted or corrected evidence could remain in synthesis.
- **Resolution:** addendum requires retraction/expression-of-concern/correction checks before synthesis.
- **Status:** resolved in protocol; execution pending.

### F16 — Pilot criteria could under-sample difficult cases

- **Severity:** high
- **Finding:** a random pilot might omit historical, mixed, contextual and family cases.
- **Resolution:** addendum requires a stratified pilot including all known difficulty classes.
- **Status:** resolved; pilot not yet drawn.

## Remaining external blockers

The internal review cannot close the following:

1. named human approval of protocol and roles;
2. time-stamped OSF registration;
3. independent PRESS review of the final search strategy;
4. access and execution of remaining databases;
5. assisted SciELO/LILACS exports;
6. independent dual human screening;
7. external/peer ROBIS and AMSTAR 2 audit;
8. statistical review of domain-specific synthesis plans.

## Recommendation

Approve protocol v2 plus normative addendum as the frozen operational basis for pilot development, but do not label G0 fully approved until named human approval and registration are documented. Do not begin production screening before the minimum conditions in addendum A16 are met.
