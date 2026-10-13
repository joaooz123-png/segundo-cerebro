from __future__ import annotations

import csv
import json
import os
import re
from collections import Counter, defaultdict
from pathlib import Path

PUBMED_MENTIONS = Path(os.environ["PFILD_PUBLICATION_REGISTRY_MENTIONS"])
OPENALEX_EXPLICIT = Path(os.environ["PFILD_OPENALEX_EXPLICIT_CANDIDATES"])
CITATION_CANDIDATES = Path(os.environ["PFILD_CITATION_CANDIDATES"])
OUTPUT_DIR = Path(os.getenv("PFILD_G3_FAMILY_OUTPUT_DIR", "g3_registry_family_map"))

PATTERNS = {
    "NCT": re.compile(r"\bNCT\d{8}\b", re.I),
    "EudraCT": re.compile(r"\b(?:EudraCT\s*)?\d{4}-\d{6}-\d{2}\b", re.I),
    "jRCT": re.compile(r"\bjRCT[a-zA-Z0-9-]+\b", re.I),
    "UMIN": re.compile(r"\bUMIN(?:-CTR)?[A-Z0-9-]*\d{5,}\b", re.I),
}


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle))


def add_link(rows: list[dict[str, str]], registry_type: str, registry_id: str,
             report_source: str, report_id: str, title: str, basis: str) -> None:
    if registry_type == "NCT":
        registry_id = registry_id.upper()
    rows.append({
        "registry_type": registry_type,
        "registry_id": registry_id,
        "report_source": report_source,
        "report_id": report_id,
        "title": title,
        "link_basis": basis,
    })


def write_csv(path: Path, rows: list[dict[str, object]], fields: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def main() -> None:
    links: list[dict[str, str]] = []

    # PubMed enrichment already extracted a broad set of registry identifiers,
    # including NCT, UMIN, jRCT, EudraCT, DRKS, ChiCTR and ISRCTN.
    for row in read_csv(PUBMED_MENTIONS):
        add_link(
            links,
            row["registry_type"],
            row["registry_id"],
            "PubMed",
            row["pmid"],
            row["title"],
            row["link_basis"],
        )

    # Supplementary OpenAlex records can expose additional trial identifiers in
    # title/abstract. These are candidate family links, never eligibility decisions.
    for row in read_csv(OPENALEX_EXPLICIT):
        text = f'{row.get("title", "")}\n{row.get("abstract", "")}'
        for registry_type, pattern in PATTERNS.items():
            for registry_id in sorted(set(pattern.findall(text))):
                add_link(
                    links, registry_type, registry_id, "OpenAlex",
                    row["openalex_id"], row["title"],
                    "explicit registry ID in title/abstract",
                )

    # Citation-candidate records currently provide title-level metadata only.
    for row in read_csv(CITATION_CANDIDATES):
        text = row.get("candidate_title", "")
        for registry_type, pattern in PATTERNS.items():
            for registry_id in sorted(set(pattern.findall(text))):
                add_link(
                    links, registry_type, registry_id, "CitationCandidate",
                    row["candidate_key"], row["candidate_title"],
                    "explicit registry ID in title",
                )

    # Exact link-level dedup only.
    unique_links: dict[tuple[str, str, str, str], dict[str, str]] = {}
    for row in links:
        key = (
            row["registry_type"], row["registry_id"],
            row["report_source"], row["report_id"],
        )
        unique_links[key] = row
    link_rows = sorted(
        unique_links.values(),
        key=lambda r: (
            r["registry_type"], r["registry_id"],
            r["report_source"], r["report_id"],
        ),
    )

    grouped: defaultdict[tuple[str, str], list[dict[str, str]]] = defaultdict(list)
    for row in link_rows:
        grouped[(row["registry_type"], row["registry_id"])].append(row)

    families: list[dict[str, object]] = []
    for (registry_type, registry_id), members in grouped.items():
        source_counts = Counter(row["report_source"] for row in members)
        titles: list[str] = []
        for member in members:
            if member["title"] and member["title"] not in titles:
                titles.append(member["title"])
        families.append({
            "registry_type": registry_type,
            "registry_id": registry_id,
            "linked_reports": len(members),
            "pubmed_reports": source_counts.get("PubMed", 0),
            "openalex_reports": source_counts.get("OpenAlex", 0),
            "citation_reports": source_counts.get("CitationCandidate", 0),
            "report_ids": "; ".join(row["report_id"] for row in members),
            "titles": " || ".join(titles[:8]),
            "relationship": "candidate study family by explicit registry identifier",
            "human_status": "not reviewed",
        })

    families.sort(
        key=lambda r: (-int(r["linked_reports"]), str(r["registry_type"]), str(r["registry_id"]))
    )

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    write_csv(
        OUTPUT_DIR / "registry_report_links_v1.csv",
        link_rows,
        ["registry_type", "registry_id", "report_source", "report_id", "title", "link_basis"],
    )
    write_csv(
        OUTPUT_DIR / "registry_family_candidates_v1.csv",
        families,
        ["registry_type", "registry_id", "linked_reports", "pubmed_reports",
         "openalex_reports", "citation_reports", "report_ids", "titles",
         "relationship", "human_status"],
    )

    counts = Counter(str(row["registry_type"]) for row in families)
    summary = {
        "registry_family_candidates": len(families),
        "explicit_report_registry_links": len(link_rows),
        "registry_type_counts": dict(counts),
        "families_with_multiple_reports": sum(int(row["linked_reports"]) >= 2 for row in families),
        "families_with_5plus_reports": sum(int(row["linked_reports"]) >= 5 for row in families),
        "largest_family": {
            "registry_type": families[0]["registry_type"] if families else None,
            "registry_id": families[0]["registry_id"] if families else None,
            "linked_reports": families[0]["linked_reports"] if families else 0,
        },
        "human_eligibility_decisions_created": 0,
        "reports_merged": 0,
        "governance": (
            "Candidate family linkage by explicit registry identifier only; "
            "reports remain distinct until human confirmation."
        ),
    }
    (OUTPUT_DIR / "registry_family_summary_v1.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    print(json.dumps(summary, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
