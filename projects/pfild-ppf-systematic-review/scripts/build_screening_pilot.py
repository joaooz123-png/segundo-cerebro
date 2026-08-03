from __future__ import annotations

import argparse
import csv
import hashlib
import json
import re
import zipfile
from collections import Counter
from pathlib import Path
from typing import Callable

SEED = "PFILD-PILOT-V1"


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle))


def write_csv(path: Path, rows: list[dict[str, object]], fields: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def stable_sample(
    records: list[dict[str, str]],
    identifier: Callable[[dict[str, str]], str],
    n: int,
) -> list[dict[str, str]]:
    return sorted(
        records,
        key=lambda record: hashlib.sha256(
            f"{identifier(record)}|{SEED}".encode("utf-8")
        ).hexdigest(),
    )[:n]


def truth(value: str) -> bool:
    return value.strip().lower() == "true"


def build(args: argparse.Namespace) -> dict[str, object]:
    output = Path(args.output)
    output.mkdir(parents=True, exist_ok=True)

    pubmed = read_csv(Path(args.pubmed))
    europe_pmc = read_csv(Path(args.europe_pmc))
    ctgov = read_csv(Path(args.ctgov))
    citations = [
        row
        for row in read_csv(Path(args.citations))
        if row.get("candidate_in_pubmed_union") == "no"
    ]

    selected: list[tuple[str, str, str, dict[str, str]]] = []
    used_pubmed: set[str] = set()

    progression = re.compile(
        r"(progress|declin|worsen).{0,60}(interstitial|fibros)|"
        r"(?:interstitial|fibros).{0,60}(progress|declin|worsen)",
        re.I,
    )
    etiology = re.compile(
        r"rheumatoid|systemic sclerosis|scleroderma|hypersensitivity|sarcoid|"
        r"myositis|connective tissue|unclassifiable|nonspecific interstitial",
        re.I,
    )
    review_type = re.compile(
        r"review|guideline|consensus|practice guideline|editorial|letter|comment",
        re.I,
    )
    trial_type = re.compile(
        r"clinical trial|randomized|randomised|controlled trial", re.I
    )

    def add_pubmed(
        stratum: str,
        predicate: Callable[[dict[str, str]], bool],
        n: int = 10,
    ) -> int:
        pool = [
            row
            for row in pubmed
            if row["pmid"] not in used_pubmed and predicate(row)
        ]
        chosen = stable_sample(pool, lambda row: row["pmid"], n)
        for row in chosen:
            used_pubmed.add(row["pmid"])
            selected.append(("PubMed", row["pmid"], stratum, row))
        return len(chosen)

    add_pubmed("PUB-CANON-PFILD", lambda r: truth(r["explicit_pfild_title"]))
    add_pubmed("PUB-CANON-PPF", lambda r: truth(r["explicit_ppf_title"]))
    add_pubmed(
        "PUB-HISTORICAL-EQUIVALENT",
        lambda r: r["publication_year"].isdigit()
        and int(r["publication_year"]) < 2017
        and bool(progression.search(r["title"] + " " + r["abstract"])),
    )
    add_pubmed(
        "PUB-IPF-ONLY-SUSPECTED", lambda r: truth(r["ipf_only_suspected_flag"])
    )
    add_pubmed("PUB-NO-ABSTRACT", lambda r: not truth(r["has_abstract"]))
    add_pubmed(
        "PUB-BROAD-LOW-PRIORITY", lambda r: r["machine_recall_priority"] == "low"
    )
    add_pubmed(
        "PUB-ETIOLOGIC-PROGRESSION",
        lambda r: bool(etiology.search(r["title"] + " " + r["abstract"]))
        and bool(progression.search(r["title"] + " " + r["abstract"]))
        and not truth(r["explicit_pfild_title"])
        and not truth(r["explicit_ppf_title"]),
    )
    add_pubmed(
        "PUB-REVIEW-GUIDELINE-OPINION",
        lambda r: bool(review_type.search(r["publication_types"] + " " + r["title"])),
    )
    add_pubmed(
        "PUB-TRIAL-INTERVENTION",
        lambda r: bool(trial_type.search(r["publication_types"] + " " + r["title"])),
    )

    if len(selected) < 90:
        pool = [row for row in pubmed if row["pmid"] not in used_pubmed]
        for row in stable_sample(pool, lambda r: r["pmid"], 90 - len(selected)):
            used_pubmed.add(row["pmid"])
            selected.append(("PubMed", row["pmid"], "PUB-TOP-UP", row))

    for source, n in (("PPR", 5), ("ETH", 2), ("AGR", 1), ("PMC", 2)):
        pool = [row for row in europe_pmc if row["source"] == source]
        for row in stable_sample(pool, lambda r: r["source_id"], n):
            selected.append(("Europe PMC", row["source_id"], f"EPMC-{source}", row))

    epmc_ids = {identifier for source, identifier, _, _ in selected if source == "Europe PMC"}
    epmc_count = sum(source == "Europe PMC" for source, _, _, _ in selected)
    if epmc_count < 10:
        pool = [row for row in europe_pmc if row["source_id"] not in epmc_ids]
        for row in stable_sample(pool, lambda r: r["source_id"], 10 - epmc_count):
            selected.append(("Europe PMC", row["source_id"], "EPMC-TOP-UP", row))

    direct_trials = [
        row
        for row in ctgov
        if re.search(
            r"progressive pulmonary fibrosis|progressive fibrosing|PF-ILD|\bPPF\b",
            " ".join(
                [row["brief_title"], row["official_title"], row["conditions"]]
            ),
            re.I,
        )
    ]
    for row in stable_sample(direct_trials, lambda r: r["nct_id"], 7):
        selected.append(("ClinicalTrials.gov", row["nct_id"], "CT-DIRECT", row))
    ct_ids = {identifier for source, identifier, _, _ in selected if source == "ClinicalTrials.gov"}
    for row in stable_sample(
        [row for row in ctgov if row["nct_id"] not in ct_ids],
        lambda r: r["nct_id"],
        3,
    ):
        selected.append(("ClinicalTrials.gov", row["nct_id"], "CT-BROAD-CONTROL", row))

    canonical = re.compile(
        r"progressive[- ](?:pulmonary fibrosis|(?:fibrosing|fibrotic)[- ]interstitial lung disease)",
        re.I,
    )
    progression_title = re.compile(
        r"(?:progressive|progression|decline).{0,60}(?:fibros|interstitial lung disease|\bILD\b)|"
        r"(?:fibros|interstitial lung disease|\bILD\b).{0,60}(?:progressive|progression|decline)",
        re.I,
    )
    direct_citations = stable_sample(
        [row for row in citations if canonical.search(row["candidate_title"])],
        lambda r: r["candidate_key"],
        2,
    )
    for row in direct_citations:
        selected.append(
            (
                "Citation candidate",
                row["candidate_key"],
                "CIT-DIRECT-OUTSIDE-UNION",
                row,
            )
        )
    direct_keys = {row["candidate_key"] for row in direct_citations}
    progression_candidates = [
        row
        for row in citations
        if row["candidate_key"] not in direct_keys
        and progression_title.search(row["candidate_title"])
    ]
    progression_candidates.sort(
        key=lambda row: (
            -int(row["number_of_sentinels"]),
            hashlib.sha256(row["candidate_key"].encode("utf-8")).hexdigest(),
        )
    )
    for row in progression_candidates[:8]:
        selected.append(
            (
                "Citation candidate",
                row["candidate_key"],
                "CIT-PROGRESSION-NETWORK",
                row,
            )
        )

    if len(selected) != 120:
        raise RuntimeError(f"Pilot must contain 120 records, found {len(selected)}")

    def convert(
        source: str, identifier: str, stratum: str, row: dict[str, str]
    ) -> dict[str, str]:
        if source == "PubMed":
            return {
                "source": source,
                "identifier": identifier,
                "title": row["title"],
                "abstract_or_summary": row["abstract"],
                "year": row["publication_year"],
                "document_type": row["publication_types"],
                "language": row["language"],
                "url": row["pubmed_url"],
                "stratum": stratum,
                "internal_metadata": json.dumps(
                    {
                        "has_abstract": row["has_abstract"],
                        "priority": row["machine_recall_priority"],
                        "ipf_only": row["ipf_only_suspected_flag"],
                        "pfild_title": row["explicit_pfild_title"],
                        "ppf_title": row["explicit_ppf_title"],
                    }
                ),
            }
        if source == "Europe PMC":
            return {
                "source": source,
                "identifier": identifier,
                "title": row["title"],
                "abstract_or_summary": row["abstract"],
                "year": row["publication_year"],
                "document_type": row["publication_type"] or row["source"],
                "language": "",
                "url": f"https://europepmc.org/article/{row['source']}/{row['source_id']}",
                "stratum": stratum,
                "internal_metadata": row["features_json"],
            }
        if source == "ClinicalTrials.gov":
            return {
                "source": source,
                "identifier": identifier,
                "title": row["brief_title"],
                "abstract_or_summary": " | ".join(
                    part
                    for part in [
                        row["official_title"],
                        row["conditions"],
                        row["interventions"],
                    ]
                    if part
                ),
                "year": (row["start_date"] or "")[:4],
                "document_type": f"{row['study_type']} {row['phases']}".strip(),
                "language": "English",
                "url": row["source_url"],
                "stratum": stratum,
                "internal_metadata": row["features_json"],
            }
        return {
            "source": source,
            "identifier": identifier,
            "title": row["candidate_title"],
            "abstract_or_summary": "",
            "year": row["candidate_year"],
            "document_type": row["candidate_source"],
            "language": "",
            "url": (
                f"https://pubmed.ncbi.nlm.nih.gov/{row['candidate_pmid']}/"
                if row["candidate_pmid"]
                else f"https://europepmc.org/article/{row['candidate_source']}/{row['candidate_id']}"
            ),
            "stratum": stratum,
            "internal_metadata": json.dumps(
                {
                    "directions": row["directions"],
                    "number_of_sentinels": row["number_of_sentinels"],
                    "sentinels": row["sentinels"],
                }
            ),
        }

    converted = [convert(*item) for item in selected]
    converted.sort(
        key=lambda row: hashlib.sha256(
            f"{row['source']}|{row['identifier']}|BLIND".encode("utf-8")
        ).hexdigest()
    )
    for index, row in enumerate(converted, start=1):
        row["pilot_id"] = f"PILOT-{index:03d}"

    reviewer_fields = [
        "pilot_id",
        "source",
        "identifier",
        "title",
        "abstract_or_summary",
        "year",
        "document_type",
        "language",
        "url",
        "decision",
        "layer",
        "exclusion_reason",
        "reviewer",
        "decision_date",
        "notes",
    ]
    reviewer_rows = []
    for row in converted:
        reviewer_rows.append(
            {
                **{field: row.get(field, "") for field in reviewer_fields},
                "decision": "Não revisado",
                "layer": "",
                "exclusion_reason": "",
                "reviewer": "",
                "decision_date": "",
                "notes": "",
            }
        )
    for reviewer in ("A", "B"):
        write_csv(
            output / f"pilot_reviewer_{reviewer}_blinded.csv",
            reviewer_rows,
            reviewer_fields,
        )

    key_fields = [
        "pilot_id",
        "source",
        "identifier",
        "stratum",
        "title",
        "internal_metadata",
    ]
    write_csv(
        output / "pilot_sampling_key_restricted.csv",
        [{field: row.get(field, "") for field in key_fields} for row in converted],
        key_fields,
    )

    files = [
        output / "pilot_reviewer_A_blinded.csv",
        output / "pilot_reviewer_B_blinded.csv",
        output / "pilot_sampling_key_restricted.csv",
    ]
    summary = {
        "version": "1.0",
        "total_records": 120,
        "source_counts": dict(Counter(row["source"] for row in converted)),
        "stratum_counts": dict(Counter(row["stratum"] for row in converted)),
        "eligibility_decisions_created": 0,
        "sampling_key_must_not_be_shown_to_screeners": True,
        "manifest": [
            {"file": path.name, "bytes": path.stat().st_size, "sha256": digest(path)}
            for path in files
        ],
    }
    (output / "pilot_summary.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    (output / "README.md").write_text(
        "# PF-ILD/PPF screening pilot v1\n\n"
        "Reviewer A and B files are identical and contain no expected eligibility answers. "
        "The sampling key must not be shown to screeners before decisions are locked.\n",
        encoding="utf-8",
    )
    with zipfile.ZipFile(output / "PFILD_PPF_piloto_triagem_v1.zip", "w", zipfile.ZIP_DEFLATED) as archive:
        for path in sorted(output.iterdir()):
            if path.name != "PFILD_PPF_piloto_triagem_v1.zip":
                archive.write(path, path.name)
    return summary


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--pubmed", required=True)
    parser.add_argument("--europe-pmc", required=True)
    parser.add_argument("--ctgov", required=True)
    parser.add_argument("--citations", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()
    print(json.dumps(build(args), ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
