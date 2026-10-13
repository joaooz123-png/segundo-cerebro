# Academic-engine saturation audit — 2026-10-13

Purpose: auxiliary sensitivity testing only. These engines are not substitutes for the named bibliographic databases in the formal protocol, and no result below creates an eligibility or PRISMA decision.

## Engines tested

- Consensus: PF-ILD/PPF query, top 10 results.
- SciSpace: four targeted semantic queries covering (1) definitions/criteria, (2) epidemiology/prognosis, (3) treatment, and (4) predictors/biomarkers.
- Scite MCP: unavailable because the connected account lacks the required paid/trial access.
- Elicit API: unavailable because the connected account lacks API access.

Access failure for Scite/Elicit is recorded as an operational limitation, never as zero results.

## Consensus reconciliation

All 10/10 returned papers mapped to the existing 2,767-PMID candidate union. One title differed only by subtitle/punctuation from PMID 33787626.

## SciSpace reconciliation

After DOI/title de-duplication across the four targeted queries, 35 unique DOI-bearing papers were audited:

- 25/35 were already in the PubMed candidate union;
- 8/35 were absent from the PubMed union but already present among the 1,210 explicit OpenAlex supplementary candidates;
- 2/35 were outside PubMed + OpenAlex explicit candidates, but both were already present in the formal sentinel citation-chasing candidate set.

The two citation-chasing-only records were:

1. PMID 36174209 — Pugashetti JV, Newton CA, Molyneaux PL, Oldham JM. *Reply to Noboa-Sevilla et al.* DOI: 10.1164/rccm.202209-1807LE. Directly relevant to the definition and timing of PPF criteria. Recovered as a forward-citation candidate from sentinels S017 and S037.
2. PMID 40786886 — Qiu Y, Ye W. *Therapeutic efficacy of pirfenidone and nintedanib in pulmonary fibrosis; a systematic review and meta-analysis.* DOI: 10.4103/atm.atm_132_25. Broader than PPF alone and therefore requires human scope judgment. Recovered as a forward-citation candidate from sentinels S005, S010 and S011.

## Interpretation

The expanded auxiliary audit found **0 records outside the combined PubMed + OpenAlex explicit + formal citation-chasing discovery universe**.

This supports search saturation but does not prove exhaustiveness. It also demonstrates why forward/backward citation chasing must remain part of the formal identification strategy: title-oblique correspondence and broader evidence syntheses can escape phrase-based database searches.

No automated include/exclude decision was generated.
