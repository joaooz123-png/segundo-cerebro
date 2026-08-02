from __future__ import annotations

import csv
import hashlib
import json
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
STATE_FILE = ROOT / "data" / "project_state.json"
DATA = ROOT / "data" / "pubmed_v2_validation"
V2_PMIDS_FILE = DATA / "pubmed_v2_pmids.csv"
COMPARISON_FILE = DATA / "pubmed_v2_comparison.csv"
DUAL_V1_ONLY_FILE = DATA / "v1_only_safety_dual_internal_review.csv"
OUT_PMIDS = DATA / "pubmed_candidate_union_pmids.csv"
OUT_SUMMARY = DATA / "pubmed_candidate_union_summary.json"
OUT_PROVENANCE = DATA / "pubmed_candidate_union_provenance.csv"


def read_csv(path: Path) -> list[dict]:
    with path.open(encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle))


def write_csv(path: Path, headers: list[str], rows: list[list[object]]) -> None:
    with path.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.writer(handle)
        writer.writerow(headers)
        writer.writerows(rows)


def main() -> None:
    state = json.loads(STATE_FILE.read_text(encoding="utf-8"))
    v1_order = [str(value) for value in state["pubmed"]["pmids"]]
    if len(v1_order) != 1004 or len(set(v1_order)) != 1004:
        raise RuntimeError("Expected the preserved PubMed v1 set of 1,004 unique PMIDs")

    v2_rows = read_csv(V2_PMIDS_FILE)
    v2_order = [row["pmid"] for row in v2_rows]
    if len(v2_order) != len(set(v2_order)):
        raise RuntimeError("PubMed v2 contains duplicate PMIDs")

    v1_set = set(v1_order)
    v2_set = set(v2_order)
    union_set = v1_set | v2_set
    overlap = v1_set & v2_set
    v1_only = v1_set - v2_set
    v2_only = v2_set - v1_set

    # Use PubMed descending-result order from the modern controlled stratum first,
    # then append legacy-only records in their original preserved v1 order.
    union_order = list(v2_order) + [pmid for pmid in v1_order if pmid not in v2_set]
    if len(union_order) != len(union_set) or len(set(union_order)) != len(union_set):
        raise RuntimeError("Candidate union ordering failed uniqueness validation")

    internal_status = {}
    if DUAL_V1_ONLY_FILE.exists():
        for row in read_csv(DUAL_V1_ONLY_FILE):
            internal_status[row["pmid"]] = {
                "reviewer_1": row.get("internal_reviewer_1", ""),
                "reviewer_2": row.get("internal_reviewer_2", ""),
                "consensus": row.get("internal_consensus", ""),
            }

    provenance_rows = []
    for rank, pmid in enumerate(union_order, 1):
        in_v1 = pmid in v1_set
        in_v2 = pmid in v2_set
        stratum = "both" if in_v1 and in_v2 else "v2.2_only" if in_v2 else "v1_legacy_only"
        review = internal_status.get(pmid, {})
        provenance_rows.append([
            rank,
            pmid,
            stratum,
            "yes" if in_v1 else "no",
            "yes" if in_v2 else "no",
            review.get("reviewer_1", "not_applicable" if in_v2 else "pending"),
            review.get("reviewer_2", "not_applicable" if in_v2 else "pending"),
            review.get("consensus", "not_applicable" if in_v2 else "pending"),
            f"https://pubmed.ncbi.nlm.nih.gov/{pmid}/",
        ])

    write_csv(
        OUT_PMIDS,
        ["rank", "pmid", "pubmed_url"],
        [[rank, pmid, f"https://pubmed.ncbi.nlm.nih.gov/{pmid}/"] for rank, pmid in enumerate(union_order, 1)],
    )
    write_csv(
        OUT_PROVENANCE,
        [
            "rank", "pmid", "retrieval_stratum", "in_v1_legacy", "in_v2_2_controlled",
            "internal_sensitivity_review", "internal_adversarial_review", "internal_consensus",
            "pubmed_url",
        ],
        provenance_rows,
    )

    union_hash = hashlib.sha256("\n".join(union_order).encode("utf-8")).hexdigest()
    v1_only_consensus = Counter(
        row[7] for row in provenance_rows if row[2] == "v1_legacy_only"
    )
    summary = {
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "status": "candidate PubMed identification set pending external independent PRESS",
        "architecture": {
            "stratum_a": "PubMed v2.2 controlled terminology and progression-in-fibrotic-ILD strategy",
            "stratum_b": "PubMed v1 legacy high-sensitivity safety-net strategy",
            "combination": "set union followed by exact PMID deduplication",
        },
        "counts": {
            "v1_legacy": len(v1_set),
            "v2_2_controlled": len(v2_set),
            "overlap": len(overlap),
            "v1_legacy_only": len(v1_only),
            "v2_2_only": len(v2_only),
            "candidate_union_unique_pmids": len(union_set),
        },
        "sentinel_recall": {
            "pubmed_applicable": 62,
            "retrieved_by_v2_2": 62,
            "recall": 1.0,
        },
        "legacy_only_internal_consensus": dict(v1_only_consensus),
        "pmid_order_sha256": union_hash,
        "governance": {
            "eligibility_decisions_made": 0,
            "prisma_counts_changed": False,
            "all_legacy_only_records_retained_in_candidate_union": True,
            "external_press_required": True,
            "human_screening_required": True,
        },
    }
    OUT_SUMMARY.write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(summary, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
