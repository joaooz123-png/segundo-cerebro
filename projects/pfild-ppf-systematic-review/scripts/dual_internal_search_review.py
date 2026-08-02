from __future__ import annotations

import csv
import json
import re
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data" / "pubmed_v2_validation"
INPUTS = {
    "precision_sample": DATA / "pubmed_v2_precision_sample_enriched.csv",
    "v1_only_safety": DATA / "pubmed_v1_only_safety_audit.csv",
}

CANONICAL_PATTERNS = [
    r"progressive[- ]fibrosing interstitial lung disease(?:s)?",
    r"progressive[- ]fibrotic interstitial lung disease(?:s)?",
    r"progressive fibrosing ild(?:s)?",
    r"progressive fibrotic ild(?:s)?",
    r"\bpf[- ]?ilds?\b",
    r"\bpfilds?\b",
    r"progressive fibrosing phenotype",
    r"progressive fibrotic phenotype",
    r"progressive fibrosis phenotype",
]
FIBROTIC_ILD_PATTERNS = [
    r"fibrosing interstitial lung disease(?:s)?",
    r"fibrotic interstitial lung disease(?:s)?",
    r"fibrosing ild(?:s)?",
    r"fibrotic ild(?:s)?",
    r"chronic fibrosing interstitial lung disease(?:s)?",
]
PROGRESSION_PATTERNS = [
    r"\bprogression\b", r"\bprogressive\b", r"\bprogressing\b",
    r"\bprogressed\b", r"disease progression", r"lung function decline",
]
MODERN_PPF_CONTEXT = [
    "progressive pulmonary fibrosis", " ppf ", "ppf)", "ppf,", "ppf.",
    "non-ipf", "non ipf", "other than idiopathic pulmonary fibrosis",
    "interstitial lung disease", "interstitial lung diseases", "fibrotic ild",
    "fibrosing ild", "inbuild", "ats/ers", "ers/jrs/alat", "progression criteria",
    "nintedanib", "pirfenidone", "nerandomilast", "antifibrotic", "anti-fibrotic",
    "approved for progressive pulmonary fibrosis", "treatment of adults with progressive pulmonary fibrosis",
]
NON_IPF_DISEASES = [
    "systemic sclerosis", "scleroderma", "rheumatoid arthritis", "connective tissue",
    "myositis", "hypersensitivity pneumonitis", "sarcoidosis", "unclassifiable",
    "autoimmune interstitial", "occupational interstitial", "fibrotic hypersensitivity",
]
EXCLUSION_CONTEXTS = [
    "paraquat", "poisoning", "acute respiratory distress", "ards", "post-covid",
    "covid-19", "bleomycin-induced", "radiotherapy-induced", "chemotherapy-induced",
    "drug-induced pulmonary fibrosis", "pulmonary thromboembolism", "rabbit model",
    "mouse model", "mice", "murine", "silica nanoparticle", "nano-silica",
    "pulmonary hypertension", "pneumoconiosis", "silicosis", "asbestosis",
]
REGULATORY_CONTEXTS = [
    "first approval", "approved", "authorisation", "authorization", "regulatory",
    "food and drug administration", "fda", "european medicines agency", "ema",
]


def has_pattern(patterns: list[str], text: str) -> bool:
    return any(re.search(pattern, text, flags=re.IGNORECASE) for pattern in patterns)


def any_term(terms: list[str], text: str) -> list[str]:
    return [term for term in terms if term in text]


def features(row: dict) -> dict:
    title = (row.get("title") or "").strip()
    abstract = (row.get("abstract") or "").strip()
    publication_types = (row.get("publication_types") or "").strip()
    title_l = f" {title.lower()} "
    abstract_l = f" {abstract.lower()} "
    combined = title_l + "\n" + abstract_l

    canonical_title = has_pattern(CANONICAL_PATTERNS, title_l)
    canonical_abstract = has_pattern(CANONICAL_PATTERNS, abstract_l)
    ppf_title = "progressive pulmonary fibrosis" in title_l
    ppf_abstract = "progressive pulmonary fibrosis" in abstract_l
    ppf_acronym = bool(re.search(r"\bppf\b", combined, flags=re.IGNORECASE))
    fibrotic_ild = has_pattern(FIBROTIC_ILD_PATTERNS, combined)
    progression = has_pattern(PROGRESSION_PATTERNS, combined)
    modern_context_hits = any_term(MODERN_PPF_CONTEXT[1:], combined)
    non_ipf_hits = any_term(NON_IPF_DISEASES, combined)
    exclusion_hits = any_term(EXCLUSION_CONTEXTS, combined)
    regulatory_hits = any_term(REGULATORY_CONTEXTS, combined)
    ipf_present = "idiopathic pulmonary fibrosis" in combined or bool(re.search(r"\bipf\b", combined))
    explicit_non_ipf = any(term in combined for term in [
        "non-ipf", "non ipf", "other than idiopathic pulmonary fibrosis",
    ])
    direct_title_focus = canonical_title or ppf_title or (
        fibrotic_ild and has_pattern(PROGRESSION_PATTERNS, title_l)
    )
    direct_abstract_focus = canonical_abstract or (
        ppf_abstract and (ppf_acronym or bool(modern_context_hits) or bool(non_ipf_hits))
    ) or (fibrotic_ild and progression)
    generic_ppf_phrase_only = (
        ppf_abstract
        and not ppf_title
        and not canonical_title
        and not canonical_abstract
        and not ppf_acronym
        and not non_ipf_hits
        and not any(term in combined for term in [
            "inbuild", "progression criteria", "ats/ers", "ers/jrs/alat",
            "approved for progressive pulmonary fibrosis",
            "treatment of adults with progressive pulmonary fibrosis",
        ])
    )
    ipf_only = (
        ipf_present
        and not explicit_non_ipf
        and not non_ipf_hits
        and not canonical_title
        and not canonical_abstract
        and not ppf_title
        and not ppf_acronym
    )
    nonhuman_signal = any(term in combined for term in [
        "mouse model", "mice", "murine", "rabbit model", "rat model", "in vitro",
    ])
    document_context = publication_types.lower()

    return {
        "canonical_title": canonical_title,
        "canonical_abstract": canonical_abstract,
        "ppf_title": ppf_title,
        "ppf_abstract": ppf_abstract,
        "ppf_acronym": ppf_acronym,
        "fibrotic_ild": fibrotic_ild,
        "progression": progression,
        "modern_context_hits": modern_context_hits,
        "non_ipf_hits": non_ipf_hits,
        "exclusion_hits": exclusion_hits,
        "regulatory_hits": regulatory_hits,
        "ipf_present": ipf_present,
        "explicit_non_ipf": explicit_non_ipf,
        "direct_title_focus": direct_title_focus,
        "direct_abstract_focus": direct_abstract_focus,
        "generic_ppf_phrase_only": generic_ppf_phrase_only,
        "ipf_only": ipf_only,
        "nonhuman_signal": nonhuman_signal,
        "publication_types": document_context,
    }


def sensitivity_reviewer(f: dict) -> tuple[str, str]:
    if f["direct_title_focus"]:
        return "retain", "Direct PF-ILD/PPF or progression-in-fibrotic-ILD focus in the title."
    if f["canonical_abstract"]:
        return "retain", "Canonical PF-ILD terminology appears in the abstract."
    if f["ppf_abstract"] and (
        f["ppf_acronym"] or f["modern_context_hits"] or f["non_ipf_hits"] or f["regulatory_hits"]
    ):
        return "retain", "PPF phrase is supported by modern clinical, non-IPF or regulatory context."
    if f["fibrotic_ild"] and f["progression"] and not f["ipf_only"]:
        return "retain", "Fibrotic ILD and progression concepts co-occur without a clear IPF-only restriction."
    if f["generic_ppf_phrase_only"] and f["exclusion_hits"]:
        return "exclude_candidate", "Generic progressive pulmonary fibrosis phrase occurs in an unrelated acute, toxic, vascular, occupational or experimental context."
    if f["ipf_only"]:
        return "exclude_candidate", "Appears restricted to IPF without separable PF-ILD/PPF content."
    if f["generic_ppf_phrase_only"] or f["nonhuman_signal"]:
        return "adjudicate", "Generic or non-human fibrosis usage requires manual contextual review."
    return "adjudicate", "Insufficient evidence for a safe automated disposition."


def adversarial_reviewer(f: dict) -> tuple[str, str]:
    if f["canonical_title"]:
        return "retain", "Canonical PF-ILD terminology is the direct title subject."
    if f["ppf_title"]:
        if f["exclusion_hits"] and not (f["ppf_acronym"] or f["non_ipf_hits"] or f["modern_context_hits"]):
            return "adjudicate", "PPF is in the title but competing context requires verification."
        return "retain", "Progressive pulmonary fibrosis is the direct title subject."
    if f["fibrotic_ild"] and has_pattern(PROGRESSION_PATTERNS, " ".join([
        "progression" if f["progression"] else "",
    ])) and (f["canonical_abstract"] or f["non_ipf_hits"] or f["ppf_acronym"]):
        return "retain", "Progression in fibrotic ILD is explicitly linked to the target construct."
    if f["regulatory_hits"] and f["ppf_abstract"]:
        return "retain", "The document directly reports a regulatory or approval event for PPF."
    if f["canonical_abstract"] and not f["exclusion_hits"] and not f["ipf_only"]:
        return "adjudicate", "Canonical terminology is present, but direct document focus must be confirmed."
    if f["generic_ppf_phrase_only"]:
        return "exclude_candidate", "Only a generic descriptive phrase appears; no modern PPF construct is established."
    if f["ipf_only"]:
        return "exclude_candidate", "IPF-only content without separable non-IPF PPF evidence."
    if f["exclusion_hits"] or f["nonhuman_signal"]:
        return "exclude_candidate", "Dominant context is acute, toxic, vascular, occupational, infectious or experimental fibrosis."
    if f["fibrotic_ild"] and f["progression"]:
        return "adjudicate", "Potential historical or implicit PF-ILD construct needs human verification."
    return "exclude_candidate", "No direct PF-ILD/PPF focus identified under a specificity-first review."


def consensus(r1: str, r2: str) -> str:
    if r1 == r2 == "retain":
        return "retain_for_human_screening"
    if r1 == r2 == "exclude_candidate":
        return "candidate_human_exclusion"
    return "internal_adjudication_required"


def read_csv(path: Path) -> list[dict]:
    with path.open(encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle))


def write_csv(path: Path, rows: list[dict], headers: list[str]) -> None:
    with path.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=headers)
        writer.writeheader()
        writer.writerows(rows)


def review_file(name: str, path: Path) -> tuple[list[dict], dict]:
    rows = read_csv(path)
    reviewed = []
    for row in rows:
        f = features(row)
        r1, reason1 = sensitivity_reviewer(f)
        r2, reason2 = adversarial_reviewer(f)
        disposition = consensus(r1, r2)
        output = dict(row)
        output["internal_reviewer_1"] = r1
        output["internal_reviewer_1_reason"] = reason1
        output["internal_reviewer_2"] = r2
        output["internal_reviewer_2_reason"] = reason2
        output["internal_consensus"] = disposition
        output["dual_review_features_json"] = json.dumps(f, ensure_ascii=False)
        reviewed.append(output)

    r1_counts = Counter(row["internal_reviewer_1"] for row in reviewed)
    r2_counts = Counter(row["internal_reviewer_2"] for row in reviewed)
    consensus_counts = Counter(row["internal_consensus"] for row in reviewed)
    agreement = sum(
        row["internal_reviewer_1"] == row["internal_reviewer_2"] for row in reviewed
    )
    summary = {
        "dataset": name,
        "n": len(reviewed),
        "reviewer_1_sensitivity_counts": dict(r1_counts),
        "reviewer_2_adversarial_counts": dict(r2_counts),
        "consensus_counts": dict(consensus_counts),
        "exact_agreement_n": agreement,
        "exact_agreement_fraction": agreement / len(reviewed) if reviewed else None,
        "prisma_decisions_made": 0,
    }
    return reviewed, summary


def main() -> None:
    summaries = {}
    for name, path in INPUTS.items():
        reviewed, summary = review_file(name, path)
        output_path = DATA / f"{name}_dual_internal_review.csv"
        headers = list(reviewed[0].keys()) if reviewed else []
        write_csv(output_path, reviewed, headers)
        summaries[name] = summary

    overall = {
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "method": (
            "Two deliberately different deterministic internal reviewers: sensitivity-first and specificity/adversarial. "
            "They are not independent human reviewers and do not alter PRISMA counts."
        ),
        "datasets": summaries,
        "gate_g1_effect": (
            "Internal evidence only. External independent PRESS remains required before formal Gate G1 approval."
        ),
    }
    (DATA / "dual_internal_review_summary.json").write_text(
        json.dumps(overall, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    print(json.dumps(overall, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
