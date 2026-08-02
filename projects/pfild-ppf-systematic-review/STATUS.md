# PF-ILD / PPF project status

Snapshot: 2026-08-02

## Durable GitHub data

- Complete reproducible PubMed search state.
- NCBI query translation.
- Complete ordered set of 1,004 unique PMIDs.
- PRISMA state: 1,004 identified/imported; 0 screened; 0 included.
- 66 discovery seeds in three JSON files.
- Publication-family and AI-governance specification.
- Executable code for deduplication, high-recall screening and Vancouver formatting.

## Master workbook

The binary XLSX remains available in the originating ChatGPT artifact session and is identified by:

- File: `PFILD_PPF_censo_bibliografico_formal_v3_pubmed.xlsx`
- Size: 128,016 bytes
- SHA-256: `2c76d373f696b2c84990c3f5d66e1ea6f70562151c4ad9d2c0b4f60762511f14`

The GitHub connector accepts UTF-8 contents but exposes no direct local-file upload action. Partial Base64 attempts were removed so the repository does not contain a misleading or corrupt workbook backup. The critical scientific data contained in the workbook are preserved in structured JSON.

## Hugging Face

Authenticated account detected: `JoaoRG`.

Intended private resources:

- Dataset: `JoaoRG/pfild-ppf-evidence-corpus`
- Space: `JoaoRG/pfild-review-agents`

The connector's Jobs/write function returned `Tool hf_jobs not found`. No Hub resource is claimed as deployed. `huggingface/bootstrap_hub.py` performs the private deployment when run with an `HF_TOKEN` that has write permission.
