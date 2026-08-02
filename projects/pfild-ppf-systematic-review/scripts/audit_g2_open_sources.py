from __future__ import annotations

import csv
import json
import re
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data" / "g2_open_sources"
PUBMED_UNION = ROOT / "data" / "pubmed_v2_validation" / "pubmed_candidate_union_pmids.csv"

CANONICAL = [
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
PPF = r"progressive pulmonary fibrosis"
ILD_CONTEXT = [
    "interstitial lung disease", "interstitial lung diseases", "fibrosing ild", "fibrotic ild",
    "non-ipf", "non ipf", "connective tissue", "systemic sclerosis", "rheumatoid arthritis",
    "hypersensitivity pneumonitis", "sarcoidosis", "unclassifiable", "autoimmune",
]
TREATMENT_CONTEXT = [
    "nintedanib", "pirfenidone", "nerandomilast", "antifibrotic", "anti-fibrotic",
    "inbuild", "progression criteria", "forced vital capacity", "fvc",
]
EXCLUSION_CONTEXT = [
    "mouse", "mice", "murine", "rat model", "rabbit", "in vitro", "paraquat", "poisoning",
    "post-covid", "covid-19", "acute respiratory distress", "pulmonary hypertension",
    "pulmonary thromboembolism", "silica nanoparticle", "nanoparticle-induced",
]


def read_csv(path: Path) -> list[dict]:
    with path.open(encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle))


def write_csv(path: Path, rows: list[dict]) -> None:
    headers = list(rows[0].keys()) if rows else []
    with path.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=headers)
        writer.writeheader()
        writer.writerows(rows)


def matches(patterns: list[str], text: str) -> bool:
    return any(re.search(pattern, text, flags=re.IGNORECASE) for pattern in patterns)


def terms(items: list[str], text: str) -> list[str]:
    return [item for item in items if item in text]


def classify_text(title: str, abstract: str, source_type: str = "") -> tuple[dict, tuple[str, str], tuple[str, str]]:
    title_l = f" {title.lower()} "
    abstract_l = f" {abstract.lower()} "
    combined = title_l + "\n" + abstract_l
    canonical_title = matches(CANONICAL, title_l)
    canonical_any = matches(CANONICAL, combined)
    ppf_title = bool(re.search(PPF, title_l, flags=re.IGNORECASE))
    ppf_any = bool(re.search(PPF, combined, flags=re.IGNORECASE))
    ild_hits = terms(ILD_CONTEXT, combined)
    treatment_hits = terms(TREATMENT_CONTEXT, combined)
    exclusion_hits = terms(EXCLUSION_CONTEXT, combined)
    ppf_acronym = bool(re.search(r"\bppf\b", combined, flags=re.IGNORECASE))
    ipf_present = "idiopathic pulmonary fibrosis" in combined or bool(re.search(r"\bipf\b", combined))
    explicit_non_ipf = any(item in combined for item in ["non-ipf", "non ipf", "other than idiopathic"])
    generic_ppf = ppf_any and not (ppf_title or canonical_any or ppf_acronym or ild_hits or treatment_hits)
    ipf_only = ipf_present and not explicit_non_ipf and not canonical_any and not ppf_title and not ild_hits

    features = {
        "canonical_title": canonical_title,
        "canonical_any": canonical_any,
        "ppf_title": ppf_title,
        "ppf_any": ppf_any,
        "ppf_acronym": ppf_acronym,
        "ild_context_hits": ild_hits,
        "treatment_context_hits": treatment_hits,
        "exclusion_context_hits": exclusion_hits,
        "generic_ppf": generic_ppf,
        "ipf_only": ipf_only,
        "source_type": source_type,
    }

    # Sensitivity-first reviewer.
    if canonical_title or ppf_title:
        r1 = ("retain", "Direct target construct in the title.")
    elif canonical_any or (ppf_any and (ppf_acronym or ild_hits or treatment_hits)):
        r1 = ("retain", "Target terminology supported by ILD, treatment or PPF context.")
    elif generic_ppf and exclusion_hits:
        r1 = ("exclude_candidate", "Generic fibrosis phrase in an unrelated context.")
    elif ipf_only:
        r1 = ("exclude_candidate", "Appears IPF-only without separable non-IPF PPF content.")
    else:
        r1 = ("adjudicate", "Insufficient information for sensitivity-safe disposition.")

    # Specificity/adversarial reviewer.
    if canonical_title or ppf_title:
        r2 = ("retain", "The title directly names PF-ILD/PPF.")
    elif canonical_any and not exclusion_hits and not ipf_only:
        r2 = ("adjudicate", "Canonical terminology exists but direct document focus must be confirmed.")
    elif ppf_any and (ppf_acronym or treatment_hits) and not exclusion_hits:
        r2 = ("adjudicate", "Potential modern PPF treatment or regulatory context.")
    else:
        r2 = ("exclude_candidate", "No sufficiently direct PF-ILD/PPF focus under specificity-first review.")

    return features, r1, r2


def consensus(r1: str, r2: str) -> str:
    if r1 == r2 == "retain":
        return "retain_for_human_screening"
    if r1 == r2 == "exclude_candidate":
        return "candidate_human_exclusion"
    return "internal_adjudication_required"


def audit_europe_pmc(pubmed_pmids: set[str]) -> tuple[list[dict], dict]:
    rows = []
    with (DATA / "europe_pmc_records.jsonl").open(encoding="utf-8") as handle:
        for line in handle:
            record = json.loads(line)
            pmid = str(record.get("pmid") or "")
            if pmid and pmid in pubmed_pmids:
                continue
            title = str(record.get("title") or "")
            abstract = str(record.get("abstractText") or "")
            source = str(record.get("source") or "")
            features, r1, r2 = classify_text(title, abstract, source)
            rows.append({
                "source": source,
                "source_id": str(record.get("id") or ""),
                "pmid": pmid,
                "pmcid": str(record.get("pmcid") or ""),
                "doi": str(record.get("doi") or ""),
                "title": title,
                "abstract": abstract,
                "publication_year": str(record.get("pubYear") or ""),
                "publication_type": str(record.get("pubType") or ""),
                "open_access": str(record.get("isOpenAccess") or ""),
                "reviewer_1": r1[0],
                "reviewer_1_reason": r1[1],
                "reviewer_2": r2[0],
                "reviewer_2_reason": r2[1],
                "internal_consensus": consensus(r1[0], r2[0]),
                "features_json": json.dumps(features, ensure_ascii=False),
                "human_decision": "not reviewed",
            })
    counts = Counter(row["internal_consensus"] for row in rows)
    source_counts = Counter(row["source"] for row in rows)
    return rows, {
        "n_non_pubmed_records": len(rows),
        "source_counts": dict(source_counts),
        "consensus_counts": dict(counts),
        "eligibility_decisions_made": 0,
    }


def audit_trials() -> tuple[list[dict], dict]:
    rows = []
    for row in read_csv(DATA / "clinicaltrials_gov_records.csv"):
        title = " ".join(filter(None, [row.get("brief_title", ""), row.get("official_title", "")]))
        abstract = " ".join(filter(None, [
            row.get("conditions", ""), row.get("interventions", ""), row.get("matched_queries", "")
        ]))
        features, r1, r2 = classify_text(title, abstract, "ClinicalTrials.gov")
        rows.append({
            **row,
            "reviewer_1": r1[0],
            "reviewer_1_reason": r1[1],
            "reviewer_2": r2[0],
            "reviewer_2_reason": r2[1],
            "internal_consensus": consensus(r1[0], r2[0]),
            "features_json": json.dumps(features, ensure_ascii=False),
            "human_decision": "not reviewed",
        })
    counts = Counter(row["internal_consensus"] for row in rows)
    statuses = Counter(row.get("overall_status", "") for row in rows)
    return rows, {
        "n_trials": len(rows),
        "consensus_counts": dict(counts),
        "overall_status_counts": dict(statuses),
        "eligibility_decisions_made": 0,
    }


def main() -> None:
    pubmed_pmids = {row["pmid"] for row in read_csv(PUBMED_UNION)}
    europe_rows, europe_summary = audit_europe_pmc(pubmed_pmids)
    trial_rows, trial_summary = audit_trials()
    write_csv(DATA / "europe_pmc_non_pubmed_dual_review.csv", europe_rows)
    write_csv(DATA / "clinicaltrials_gov_dual_review.csv", trial_rows)
    summary = {
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "method": "two deterministic internal review passes; no human or PRISMA decisions",
        "europe_pmc_non_pubmed": europe_summary,
        "clinicaltrials_gov": trial_summary,
        "next_step": "human screening later; cross-source deduplication and family linkage under Gate G3",
    }
    (DATA / "g2_internal_review_summary.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    print(json.dumps(summary, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
