from __future__ import annotations

import csv
import json
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SEED_FILE = ROOT / "data" / "seeds" / "seeds-02.json"
LOG_FILE = ROOT / "data" / "metadata_corrections.csv"

CORRECTION = {
    "seed_id": "S029",
    "title": "Progression of fibrosing interstitial lung disease",
    "doi": "10.1186/s12931-020-1296-3",
    "old_pmid": "32019572",
    "new_pmid": "31996266",
    "old_url": "https://pubmed.ncbi.nlm.nih.gov/32019572/",
    "new_url": "https://pubmed.ncbi.nlm.nih.gov/31996266/",
    "reason": (
        "PMID 32019572 resolves to an unrelated leflunomide/methotrexate toxicity case report. "
        "DOI 10.1186/s12931-020-1296-3 and the article title resolve to PMID 31996266."
    ),
    "verification_sources": (
        "NCBI PubMed identifier resolution; DOI resolution; Amass BiomedCore cross-check"
    ),
}


def main() -> None:
    records = json.loads(SEED_FILE.read_text(encoding="utf-8"))
    matches = [row for row in records if row.get("seed_id") == CORRECTION["seed_id"]]
    if len(matches) != 1:
        raise RuntimeError(f"Expected exactly one S029 record, found {len(matches)}")

    row = matches[0]
    if row.get("title") != CORRECTION["title"] or row.get("doi") != CORRECTION["doi"]:
        raise RuntimeError("S029 title/DOI do not match the correction specification")

    changed = False
    if row.get("pmid_or_registry") == CORRECTION["old_pmid"]:
        row["pmid_or_registry"] = CORRECTION["new_pmid"]
        row["source_url"] = CORRECTION["new_url"]
        row["legal_fulltext"] = "PMC/publisher located"
        changed = True
    elif row.get("pmid_or_registry") != CORRECTION["new_pmid"]:
        raise RuntimeError(f"Unexpected S029 PMID: {row.get('pmid_or_registry')}")

    if changed:
        SEED_FILE.write_text(
            json.dumps(records, ensure_ascii=False, separators=(",", ":")),
            encoding="utf-8",
        )

    headers = [
        "timestamp_utc", "seed_id", "field", "old_value", "new_value",
        "reason", "verification_sources", "changed_in_this_run",
    ]
    existing = []
    if LOG_FILE.exists():
        with LOG_FILE.open(encoding="utf-8-sig", newline="") as handle:
            existing = list(csv.DictReader(handle))

    correction_key = (
        CORRECTION["seed_id"], "pmid_or_registry",
        CORRECTION["old_pmid"], CORRECTION["new_pmid"],
    )
    already_logged = any(
        (item.get("seed_id"), item.get("field"), item.get("old_value"), item.get("new_value")) == correction_key
        for item in existing
    )
    if not already_logged:
        existing.append({
            "timestamp_utc": datetime.now(timezone.utc).isoformat(),
            "seed_id": CORRECTION["seed_id"],
            "field": "pmid_or_registry",
            "old_value": CORRECTION["old_pmid"],
            "new_value": CORRECTION["new_pmid"],
            "reason": CORRECTION["reason"],
            "verification_sources": CORRECTION["verification_sources"],
            "changed_in_this_run": "yes" if changed else "no",
        })
        with LOG_FILE.open("w", encoding="utf-8-sig", newline="") as handle:
            writer = csv.DictWriter(handle, fieldnames=headers)
            writer.writeheader()
            writer.writerows(existing)

    print(json.dumps({
        "seed_id": CORRECTION["seed_id"],
        "old_pmid": CORRECTION["old_pmid"],
        "new_pmid": CORRECTION["new_pmid"],
        "changed": changed,
        "log": str(LOG_FILE.relative_to(ROOT)),
    }, indent=2))


if __name__ == "__main__":
    main()
