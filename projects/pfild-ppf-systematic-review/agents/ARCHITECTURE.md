# Internal evidence-review assistants

The Hugging Face workspace is designed around three bounded assistants. None of them may make a final inclusion decision without human confirmation.

## 1. Deduplication assistant

Inputs: title, authors, year, DOI, PMID, abstract and source database.

Methods:
- exact DOI and PMID matching;
- normalized title and author matching;
- fuzzy title similarity;
- semantic title/abstract similarity using `sentence-transformers/all-MiniLM-L6-v2`;
- publication-family detection kept separate from bibliographic duplication.

Outputs: duplicate probability, matched record, evidence and recommended action.

## 2. High-recall screening assistant

Inputs: title and abstract.

Methods:
- deterministic PF-ILD/PPF terminology rules;
- zero-shot classification using `MoritzLaurer/deberta-v3-base-zeroshot-v1.1-all-33`;
- mandatory uncertainty flag when PPF could mean another concept, IPF-only populations are inseparable, or progression is merely incidental.

Outputs: include / exclude / uncertain recommendation, confidence and explicit reasons. Human review remains mandatory.

## 3. Vancouver metadata assistant

Inputs: DOI, PMID, ISBN, trial ID and bibliographic metadata.

Methods:
- identifier normalization;
- all-author preservation;
- journal-title abbreviation verification;
- Vancouver rendering with first six authors plus `et al.` only in the formatted reference;
- missing-field and inconsistency flags.

Outputs: structured metadata, formatted citation and unresolved QA fields.

## Governance

- AI recommendations are never treated as final screening decisions.
- Every transformation must preserve the source record and provenance.
- No paywall circumvention is implemented.
- Full text is stored only when legally supplied or openly licensed.