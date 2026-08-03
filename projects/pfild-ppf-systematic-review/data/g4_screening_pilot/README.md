# Screening calibration pilot v1

## Purpose

Prepare, but do not begin, independent human screening. The pilot is designed to reveal disagreements in construct interpretation before production screening.

## Composition

The deterministic pilot contains 120 records:

- 90 PubMed reports;
- 10 Europe PMC records not represented by PMID in the PubMed union;
- 10 ClinicalTrials.gov records;
- 10 citation-network candidates outside the PubMed union.

It deliberately includes:

- explicit PF-ILD and PPF terminology;
- historical-equivalent progression concepts;
- suspected IPF-only records;
- records without abstracts;
- low-priority broad-recall records;
- etiology-specific progression without canonical PPF wording;
- reviews, guidelines, editorials and correspondence;
- trials and registry records;
- preprints, theses, AGRICOLA and PMC-only records;
- citation candidates with direct terminology or high network support.

## Blinding

The package contains:

- `pilot_reviewer_A_blinded.csv`;
- `pilot_reviewer_B_blinded.csv`;
- `pilot_sampling_key_restricted.csv`.

The reviewer files are identical and contain no expected decision or gold-standard answer. Reviewers must work independently and should not access the sampling key until both decision files are locked.

The sampling key describes only how records were selected and the machine metadata used to ensure difficult strata were represented. It is not an eligibility answer key.

## Allowed decisions

Use the operational screening manual:

- advance — direct evidence;
- advance — essential context;
- exclude with observable reason;
- uncertain.

## Required procedure

1. Name reviewers A and B.
2. Confirm both have approved protocol v2 and the Portuguese screening manual.
3. Give each reviewer only their blinded CSV.
4. Lock completed files with checksums before comparison.
5. Join by `pilot_id`.
6. Calculate raw agreement and Cohen kappa, without treating kappa as sufficient by itself.
7. Discuss every disagreement and identify systematic misunderstanding.
8. Record operational clarifications in the amendment log.
9. Repeat calibration if a material rule changes.
10. Production screening may begin only after the guarantor approves calibration.

## Generation

The deterministic selection algorithm is in:

`projects/pfild-ppf-systematic-review/scripts/build_screening_pilot.py`

It requires the frozen PubMed metadata, Europe PMC non-PubMed records, ClinicalTrials.gov review set and citation-candidate dataset.

## Methodological status

- eligibility decisions created: 0;
- gold-standard decisions created: 0;
- production screening started: no;
- G4 remains not started until humans complete and approve the pilot.
