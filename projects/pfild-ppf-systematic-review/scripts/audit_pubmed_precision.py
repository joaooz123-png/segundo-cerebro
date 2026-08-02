from __future__ import annotations

import csv
import json
import os
import re
import time
import urllib.error
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data" / "pubmed_v2_validation"
SAMPLE_FILE = DATA / "pubmed_v2_precision_sample.csv"
COMPARISON_FILE = DATA / "pubmed_v2_comparison.csv"

BASE = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/"
EMAIL = os.getenv("NCBI_EMAIL", "pfild-review@example.invalid")
API_KEY = os.getenv("NCBI_API_KEY", "").strip()
TOOL = "pfild_ppf_precision_audit"

CORE_PATTERNS = [
    r"progressive[- ]fibrosing interstitial lung disease(?:s)?",
    r"progressive[- ]fibrotic interstitial lung disease(?:s)?",
    r"progressive fibrosing ild(?:s)?",
    r"progressive fibrotic ild(?:s)?",
    r"\bpf[- ]?ilds?\b",
    r"\bpfilds?\b",
    r"progressive pulmonary fibrosis",
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
NON_IPF_TERMS = [
    "non-ipf", "non ipf", "connective tissue", "systemic sclerosis", "scleroderma",
    "rheumatoid arthritis", "myositis", "hypersensitivity pneumonitis", "sarcoidosis",
    "unclassifiable", "autoimmune", "occupational", "fibrotic ild", "fibrosing ild",
    "interstitial lung diseases", "interstitial lung disease",
]
CONTEXT_TERMS = [
    "nintedanib", "pirfenidone", "antifibrotic", "anti-fibrotic", "inbuild",
    "progression criteria", "forced vital capacity", "fvc decline", "fibrotic phenotype",
]
UNRELATED_ACUTE_TERMS = [
    "paraquat", "poisoning", "acute respiratory distress", "post-covid", "covid-19",
    "bleomycin-induced", "radiotherapy", "chemotherapy", "drug-induced", "mouse", "mice",
]


def post(endpoint: str, params: dict[str, str], retries: int = 6) -> bytes:
    payload = dict(params)
    payload.update({"tool": TOOL, "email": EMAIL})
    if API_KEY:
        payload["api_key"] = API_KEY
    request = urllib.request.Request(
        BASE + endpoint,
        data=urllib.parse.urlencode(payload).encode("utf-8"),
        headers={"User-Agent": f"{TOOL}/1.0 ({EMAIL})"},
        method="POST",
    )
    for attempt in range(retries):
        try:
            with urllib.request.urlopen(request, timeout=120) as response:
                return response.read()
        except (urllib.error.HTTPError, urllib.error.URLError, TimeoutError):
            if attempt + 1 == retries:
                raise
            time.sleep(min(2 ** attempt, 30))
    raise RuntimeError("Unreachable")


def chunks(items: list[str], size: int):
    for start in range(0, len(items), size):
        yield items[start:start + size]


def text_of(element: ET.Element | None) -> str:
    if element is None:
        return ""
    return "".join(element.itertext()).strip()


def fetch_records(pmids: list[str]) -> dict[str, dict]:
    result: dict[str, dict] = {}
    for batch in chunks(pmids, 80):
        raw = post("efetch.fcgi", {
            "db": "pubmed",
            "retmode": "xml",
            "id": ",".join(batch),
        })
        root = ET.fromstring(raw)
        for item in list(root.findall("PubmedArticle")) + list(root.findall("PubmedBookArticle")):
            pmid_node = item.find(".//PMID")
            pmid = text_of(pmid_node)
            if not pmid:
                continue
            title = text_of(item.find(".//ArticleTitle")) or text_of(item.find(".//BookDocument/ArticleTitle"))
            abstract_parts = []
            for node in item.findall(".//Abstract/AbstractText"):
                label = node.attrib.get("Label") or node.attrib.get("NlmCategory") or ""
                body = text_of(node)
                abstract_parts.append(f"{label}: {body}" if label and body else body)
            publication_types = [text_of(node) for node in item.findall(".//PublicationType") if text_of(node)]
            result[pmid] = {
                "pmid": pmid,
                "title": title,
                "abstract": "\n".join(part for part in abstract_parts if part),
                "publication_types": "; ".join(dict.fromkeys(publication_types)),
            }
        time.sleep(0.12 if API_KEY else 0.36)
    return result


def matches_any(patterns: list[str], text: str) -> list[str]:
    return [pattern for pattern in patterns if re.search(pattern, text, flags=re.IGNORECASE)]


def classify(record: dict) -> tuple[str, str, dict]:
    title = record.get("title", "")
    abstract = record.get("abstract", "")
    combined = f"{title}\n{abstract}".lower()
    title_lower = title.lower()

    core_hits = matches_any(CORE_PATTERNS, combined)
    fibrotic_hits = matches_any(FIBROTIC_ILD_PATTERNS, combined)
    progression_hits = matches_any(PROGRESSION_PATTERNS, combined)
    non_ipf_hits = [term for term in NON_IPF_TERMS if term in combined]
    context_hits = [term for term in CONTEXT_TERMS if term in combined]
    acute_hits = [term for term in UNRELATED_ACUTE_TERMS if term in combined]
    ipf_present = "idiopathic pulmonary fibrosis" in combined or re.search(r"\bipf\b", combined)
    explicit_non_ipf = any(term in combined for term in ["non-ipf", "non ipf", "other than idiopathic pulmonary fibrosis"])
    ipf_only_suspected = bool(ipf_present and not explicit_non_ipf and not core_hits and not any(
        term in combined for term in NON_IPF_TERMS if term not in {"interstitial lung disease", "interstitial lung diseases"}
    ))

    if core_hits:
        label = "core_explicit"
        reason = "Explicit PF-ILD/PPF or progressive fibrotic phenotype terminology."
    elif fibrotic_hits and progression_hits and not ipf_only_suspected:
        label = "probable_relevant"
        reason = "Fibrotic/fibrosing ILD and progression concepts co-occur without an IPF-only signal."
    elif (non_ipf_hits and context_hits and not ipf_only_suspected) or (
        "interstitial lung disease" in combined and progression_hits and not ipf_only_suspected
    ):
        label = "contextual_or_uncertain"
        reason = "Potential non-IPF ILD progression or antifibrotic context; human review required."
    elif ipf_only_suspected:
        label = "likely_irrelevant_ipf_only"
        reason = "Appears focused on idiopathic pulmonary fibrosis without separable non-IPF PF-ILD/PPF content."
    elif acute_hits and not core_hits:
        label = "likely_irrelevant_other_fibrosis"
        reason = "Acute, toxic, treatment-induced, infectious or experimental fibrosis context rather than chronic non-IPF PPF."
    else:
        label = "likely_irrelevant_or_incidental"
        reason = "No direct PF-ILD/PPF focus detected; may be incidental or generic fibrosis literature."

    features = {
        "core_hits": core_hits,
        "fibrotic_ild_hits": fibrotic_hits,
        "progression_hits": progression_hits,
        "non_ipf_hits": non_ipf_hits,
        "context_hits": context_hits,
        "acute_or_other_hits": acute_hits,
        "ipf_only_suspected": ipf_only_suspected,
        "explicit_term_in_title": bool(matches_any(CORE_PATTERNS, title_lower)),
    }
    return label, reason, features


def read_csv(path: Path) -> list[dict]:
    with path.open(encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle))


def write_csv(path: Path, rows: list[dict], headers: list[str]) -> None:
    with path.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=headers)
        writer.writeheader()
        writer.writerows(rows)


def audit(pmids: list[str], source_class: dict[str, str]) -> list[dict]:
    records = fetch_records(pmids)
    rows = []
    for pmid in pmids:
        record = records.get(pmid, {"pmid": pmid, "title": "", "abstract": "", "publication_types": ""})
        label, reason, features = classify(record)
        rows.append({
            "pmid": pmid,
            "source_class": source_class.get(pmid, ""),
            "title": record.get("title", ""),
            "abstract": record.get("abstract", ""),
            "publication_types": record.get("publication_types", ""),
            "machine_label": label,
            "machine_reason": reason,
            "explicit_term_in_title": features["explicit_term_in_title"],
            "ipf_only_suspected": features["ipf_only_suspected"],
            "feature_evidence_json": json.dumps(features, ensure_ascii=False),
            "internal_reviewer_1": "pending",
            "internal_reviewer_1_reason": "",
            "internal_reviewer_2": "pending",
            "internal_reviewer_2_reason": "",
            "human_decision": "not reviewed",
            "pubmed_url": f"https://pubmed.ncbi.nlm.nih.gov/{pmid}/",
        })
    return rows


def main() -> None:
    sample = read_csv(SAMPLE_FILE)
    comparison = read_csv(COMPARISON_FILE)
    source_class = {row["pmid"]: row["classification"] for row in comparison}
    sample_pmids = [row["pmid"] for row in sample]
    v1_only_pmids = [row["pmid"] for row in comparison if row["classification"] == "v1_only"]

    sample_rows = audit(sample_pmids, source_class)
    v1_only_rows = audit(v1_only_pmids, source_class)

    headers = [
        "pmid", "source_class", "title", "abstract", "publication_types",
        "machine_label", "machine_reason", "explicit_term_in_title",
        "ipf_only_suspected", "feature_evidence_json",
        "internal_reviewer_1", "internal_reviewer_1_reason",
        "internal_reviewer_2", "internal_reviewer_2_reason",
        "human_decision", "pubmed_url",
    ]
    write_csv(DATA / "pubmed_v2_precision_sample_enriched.csv", sample_rows, headers)
    write_csv(DATA / "pubmed_v1_only_safety_audit.csv", v1_only_rows, headers)

    sample_counts = Counter(row["machine_label"] for row in sample_rows)
    v1_only_counts = Counter(row["machine_label"] for row in v1_only_rows)
    likely_relevant = sample_counts["core_explicit"] + sample_counts["probable_relevant"]
    possible_relevant = likely_relevant + sample_counts["contextual_or_uncertain"]

    summary = {
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "status": "machine pre-audit only; no eligibility or PRISMA decisions",
        "precision_sample": {
            "n": len(sample_rows),
            "label_counts": dict(sample_counts),
            "high_confidence_relevance_fraction": likely_relevant / len(sample_rows) if sample_rows else None,
            "upper_bound_including_uncertain": possible_relevant / len(sample_rows) if sample_rows else None,
            "sampling_seed": 20260802,
        },
        "v1_only_safety_set": {
            "n": len(v1_only_rows),
            "label_counts": dict(v1_only_counts),
            "machine_flagged_for_internal_review": sum(
                v1_only_counts[label] for label in ["core_explicit", "probable_relevant", "contextual_or_uncertain"]
            ),
        },
        "next_required_steps": [
            "complete two independent internal AI reviews of all 100 precision-sample records",
            "resolve internal disagreements without changing PRISMA counts",
            "human-review all machine-flagged v1-only records before deciding whether the union search is required",
            "send the final candidate strategy and evidence package for external independent PRESS review",
        ],
    }
    (DATA / "pubmed_precision_audit_summary.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
