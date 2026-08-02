# PF-ILD / PPF systematic evidence census

Versioned workspace for the systematic census of all retrievable indexed literature on **progressive fibrosing interstitial lung disease (PF-ILD)** and the subsequent **progressive pulmonary fibrosis (PPF)** terminology in non-IPF fibrotic interstitial lung diseases.

## Current formal state — 2 August 2026

- PubMed/MEDLINE search executed without date, language, design or document-type filters.
- 1,004 unique PMIDs formally imported.
- 0 records screened.
- 0 reports included or excluded.
- 66 verified discovery seeds remain separate from PRISMA counts.
- 52 discovery seeds were reconciled with the formal PubMed import.

## Repository layout

- `data/project_state.json`: reproducible PubMed query, NCBI translation, complete PMID set and PRISMA state.
- `data/seeds/`: all discovery seeds with authors, DOI/PMID, document type and family links.
- `references/`: RIS references with verified metadata.
- `agents/`: specifications for internal Hugging Face assistants.

## Methodological constraints

1. Historical PF-ILD criteria and the 2022 PPF criteria remain analytically distinct.
2. IPF is not part of the core non-IPF population unless data are separable or contextual.
3. Bibliographic duplicates are distinguished from multiple reports belonging to one study family.
4. All authors are preserved in structured data. `Et al.` is used only in displayed Vancouver citations.
5. PRISMA counts are updated only from complete, reproducible database exports.
6. Automated screening and deduplication are decision-support tools; final decisions require human review.

## Search concept

The master query includes PF-ILD, PFILD, progressive fibrosing/fibrotic ILD, progressive fibrotic phenotype and PPF linked to interstitial lung disease/fibrosis terminology. No intervention, prognosis, biomarker or etiology block is required for retrieval.

## Backup note

The connected GitHub writer cannot create a brand-new repository or upload binary files directly. This dedicated branch is therefore the durable GitHub workspace. The complete scientific state is stored as text-first, reconstructable data; the local XLSX checksum is recorded in `data/project_state.json`.