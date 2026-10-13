from __future__ import annotations

import csv
import re
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PATH = ROOT / "search" / "grey" / "GREY_SOURCE_SENTINELS_V1.csv"

with PATH.open(encoding="utf-8-sig", newline="") as handle:
    rows = list(csv.DictReader(handle))

assert len(rows) == 41, len(rows)
ids = [row["sentinel_id"] for row in rows]
assert len(ids) == len(set(ids)), "duplicate sentinel IDs"

counts = Counter(row["source_to_validate"] for row in rows)
assert counts["ATS International Conference abstracts"] == 15, counts
assert counts["ERS conference abstracts"] == 20, counts
assert counts["BDTD/IBICT"] == 6, counts

for row in rows:
    assert row["expected_retrieval"] == "Yes", row
    assert row["eligibility_status"] == "Not assessed", row
    assert row["title"].strip(), row
    assert row["source_url"].strip(), row
    if row["sentinel_id"].startswith("GREY-ATS-"):
        assert re.fullmatch(r"10\.1164/ajrccm\.\d{4}\.\d+\.abstracts\.[a-z]\d+", row["doi"], re.I), row
    elif row["sentinel_id"].startswith("GREY-ERS-"):
        assert re.fullmatch(r"10\.1183/13993003\.congress-\d{4}\.[a-z]*\d+", row["doi"], re.I), row
    elif row["sentinel_id"].startswith("GREY-BDTD-"):
        assert "bdtd.ibict.br" in row["source_url"], row

print({
    "sentinels": len(rows),
    "ATS": counts["ATS International Conference abstracts"],
    "ERS": counts["ERS conference abstracts"],
    "BDTD": counts["BDTD/IBICT"],
    "eligibility_decisions": 0,
})
