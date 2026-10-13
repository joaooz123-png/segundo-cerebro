# Independent PRESS reviewer instructions — PF-ILD / PPF

Prepared: 2026-10-13

## Purpose

This form supports independent peer review of the search strategy. It does not replace the reviewer’s professional judgment and does not convert internal validation into external PRESS approval.

The six core PRESS 2015 domains are represented explicitly:
1. translation of the research question into searchable concepts;
2. Boolean/proximity logic;
3. subject headings;
4. text words;
5. spelling/syntax/field construction;
6. limits and filters.

Additional project-specific rows cover validation, multibase translation, regional sources, registries, citation searching, grey literature and PRISMA-S reproducibility.

## Reviewer materials

Primary package:
- `methods/PRESS_EXTERNAL_REVIEW_PACKAGE_V2.md` (superseded by V3 once issued);
- `search/pubmed_v2_candidate.txt`;
- `data/pubmed_v2_validation/pubmed_v2_validation.json`;
- `data/pubmed_v2_validation/pubmed_v2_sentinel_validation.csv`;
- `data/metadata_corrections.csv`;
- `search/subscription/*.txt`;
- `search/manual_exports/*`;
- `search/grey/*`;
- `search/SEARCH_EXECUTION_MANIFEST.csv`.

Assessment form:
- `methods/PRESS_EXTERNAL_REVIEW_FORM_V1.csv`.

## Rating convention

Use one of:
- **no issue** — no change required;
- **minor** — desirable correction unlikely to materially change recall;
- **major** — correction could materially affect recall/precision or reproducibility;
- **not applicable**.

For each non-trivial comment, cite the exact database, search line/block or file and describe the recommended replacement.

## Independence

The reviewer should not be one of the people or agents who authored or internally audited the strategy. Internal AI/adversarial checks are disclosed but do not count as independent PRESS.

## Change control

Every accepted recommendation that changes retrieval must produce:
- a new immutable strategy version;
- an amendment-log entry;
- a new execution date/count/export/checksum where already executed;
- preservation of the superseded strategy and output.

Do not overwrite prior search versions.
