# Regenerating Gate G3 exact deduplication

## Immutable inputs
- `data/project_state.json` and the PubMed v2.2 candidate union from Gate G1.
- Europe PMC full export from Gate G2.
- ClinicalTrials.gov full export from Gate G2.
- TrialCore/WHO ICTRP supplementary registry captures.
- FDA and EMA regulatory source register.

## Identifier normalization
- PMID: digits only.
- PMCID: uppercase canonical identifier.
- DOI: lowercase; remove `doi:`, `https://doi.org/`, terminal spaces and punctuation.
- Titles: Unicode NFKD, lowercase, remove punctuation, normalize whitespace.
- Registry IDs: uppercase; preserve the source registry's native value.

## Safe automatic collapse
A retrieval-source duplicate may be collapsed only when:
1. the PMID is identical; or
2. DOI, normalized title, authorship/version and document type all agree without conflict.

Preserve every retrieval source in the provenance field.

## Never collapse automatically
- Same DOI with different PMIDs or report types.
- Preprint versus journal article.
- Protocol versus primary report.
- Primary report versus subgroup, extension, safety analysis or post-marketing report.
- Letter, reply, correction or editorial related to a primary report.
- Country-specific trial registrations.
- Regulatory document versus scientific publication.

## Family linkage
Create reversible candidate links using:
- exact NCT/EudraCT/registry identifiers in title, abstract or metadata;
- exact normalized title;
- sponsor, intervention, enrollment, dates and protocol root;
- preprint and journal-title equivalence.

Each link must include evidence, confidence and `human_status=not reviewed`.

## Current internal results
- 4,066 raw retrieval units across the sources currently captured.
- 1,072 Europe PMC records match the PubMed candidate union by exact PMID.
- 1 safe same-DOI/same-title source-representation group.
- 1 DOI collision group containing four distinct NEJM correspondence records.
- 25 exact-title clusters, including 15 preprint-to-publication family candidates.
- 57 exact publication-to-NCT links.
- 22 selected non-US registry records across 14 protocol roots.

No eligibility or PRISMA count is changed by this procedure.
