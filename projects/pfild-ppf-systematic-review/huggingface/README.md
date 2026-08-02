---
title: PF-ILD Review Agents
emoji: 🫁
colorFrom: blue
colorTo: teal
sdk: gradio
app_file: app.py
pinned: false
license: apache-2.0
---

# PF-ILD / PPF Review Agents

Private decision-support workspace for the systematic evidence census of progressive fibrosing interstitial lung disease and progressive pulmonary fibrosis in non-IPF fibrotic ILD.

## Assistants

1. **Deduplicator** — exact DOI/PMID comparison, normalized-title similarity and semantic similarity with `sentence-transformers/all-MiniLM-L6-v2`.
2. **High-recall screener** — explicit PF-ILD/PPF terminology plus zero-shot classification with `MoritzLaurer/deberta-v3-base-zeroshot-v1.1-all-33`.
3. **Vancouver formatter** — preserves the full author list and uses the first six authors followed by `et al.` only in the rendered reference.

## Governance

- No autonomous final inclusion or exclusion.
- Every decision must retain the original record and provenance.
- Bibliographic duplicates and publication-family links are different concepts.
- Historical PF-ILD definitions and the 2022 PPF definition remain analytically distinct.
- IPF-only records require separable non-IPF data or explicit contextual classification.
- No paywall circumvention.

## Intended private Hub resources

- Dataset: `JoaoRG/pfild-ppf-evidence-corpus`
- Space: `JoaoRG/pfild-review-agents`

The ChatGPT Hugging Face connector recognized the account `JoaoRG`, but its Jobs/write action returned `Tool hf_jobs not found` on 2 August 2026. Therefore these Hub resources must not be considered deployed until the bootstrap script completes successfully.
