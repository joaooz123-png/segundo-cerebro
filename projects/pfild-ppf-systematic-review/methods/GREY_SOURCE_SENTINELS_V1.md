# PF-ILD/PPF grey-literature source validation sentinels v1

Generated: 2026-10-13

Purpose: validate execution sensitivity of source-specific ATS, ERS, and BDTD searches. These records are **not preclassified as eligible** and must not be counted as included evidence.

## Construction

- ATS: all 15 no-PMID OpenAlex conference records with ATS/AJRCCM meeting-abstract DOI patterns and direct PF-ILD/PPF terminology in the title.
- ERS: deterministic 20-record sample from no-PMID OpenAlex records with ERS Congress DOI patterns and direct PF-ILD/PPF terminology in the title, spread across sorted year/title positions.
- BDTD: all 6 high/medium-priority records from the initial partial BDTD execution; 2 exact-term and 4 conceptual-sensitivity sentinels.

## Rule

Every source-specific execution should retrieve all sentinels applicable to that source. A miss triggers investigation of platform syntax, indexing, source coverage, or record metadata. Query changes prompted by a miss must be logged as an amendment and versioned before rerun.

This sentinel set was derived after the source-specific strategies were prepared; it is therefore a validation set, not a justification for silently rewriting those strategies. If a strategy is changed to improve recovery, the change must be recorded prospectively as an amendment and rerun as a new immutable version.

CSV SHA-256: `a7f468aad228c8c8260e921fece980257b852b7218a507512f5f115d8025489e`
