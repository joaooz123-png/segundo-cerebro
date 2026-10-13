# PF-ILD / PPF grey-literature execution protocol v1

Date prepared: 2026-10-13

## Purpose

Close the grey-literature/conference/thesis component of Gate G2 without treating a discovery index as a substitute for source-specific searching.

This protocol supplements — but does not replace — the bibliographic databases, trial registries, Europe PMC, citation chasing, regulatory sources, LILACS/SciELO, and OpenAlex supplementary discovery.

## Sources

1. **ERS conference abstracts**
   - official ERS publications platform;
   - strategy: `search/grey/ers_conference_v1.txt`;
   - search all conference-abstract content exposed by the platform, not only ILD sessions.

2. **ATS International Conference abstracts**
   - ATS Journals / AJRCCM meeting abstracts;
   - strategy: `search/grey/ats_conference_v1.txt`;
   - search the entire meeting-abstract archive.

3. **ProQuest Dissertations & Theses Global**
   - database-specific command-line strategy;
   - strategy: `search/grey/proquest_dissertations_v1.txt`;
   - execute if institutional access is available.

4. **BDTD / IBICT**
   - Brazilian thesis/dissertation source;
   - automated reproducible collector: `scripts/collect_bdtd_theses.py`;
   - source status must be determined from the corresponding GitHub Actions artifact.

5. **OpenAlex**
   - supplementary discovery only;
   - must never be described as a replacement for conference archives or dissertation databases;
   - only a completed, scoped title/abstract run may be entered as executed.

## Required evidence for each executed source

For each source capture:
- source/database and platform;
- execution date and local time with timezone;
- exact query/stratum;
- search-history or query URL/identifier;
- displayed hit count for every stratum;
- total exported records before deduplication;
- unmodified source-native export;
- export format;
- SHA-256 of raw export;
- screenshots/HTML/search-history evidence when the platform does not provide a reusable history;
- executor;
- any source-access error.

## Search restrictions

Do **not** impose:
- publication-year limits;
- language limits;
- country limits;
- underlying ILD restrictions;
- treatment/outcome restrictions;
- study-design restrictions.

A platform filter that limits a dedicated source to its intended **record class** (for example, ERS “Conference abstract” or PQDT Global dissertations/theses) is a provenance/source filter and is allowed.

## Deduplication governance

Never discard a report during source export.

After import:
- exact PMID or another unambiguous source identifier may identify duplicate source representations;
- DOI alone does not authorize merging when titles, document types, versions or PMIDs conflict;
- conference abstract -> journal article is a publication-family relationship, not an automatic duplicate;
- dissertation/thesis -> journal article is a family relationship, not an automatic duplicate;
- protocol -> results paper, letter, correction, preprint and secondary analysis remain separate reports.

## Eligibility governance

Machine processing may rank and propose links only. It may not create final inclusion/exclusion decisions. PRISMA identification counts remain unchanged until the full source set is frozen and human-confirmed deduplication is complete.
