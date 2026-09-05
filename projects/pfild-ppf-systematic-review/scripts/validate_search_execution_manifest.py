from __future__ import annotations

import csv
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT / "search" / "SEARCH_EXECUTION_MANIFEST.csv"
OUT = ROOT / "artifacts" / "search_execution_manifest_validation.json"

EXECUTED_STATUSES = {"executed", "executed_internal_validation"}
PREPARED_STATUSES = {"prepared_not_executed", "manual_export_required"}
REQUIRED_COLUMNS = {
    "source_id", "database", "platform", "strategy_file", "strategy_version", "status",
    "execution_date_local", "timezone", "displayed_hit_count", "exported_record_count",
    "raw_export_filename", "raw_export_format", "raw_export_sha256", "executor", "press_status", "notes",
}


def main() -> None:
    with MANIFEST.open(encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        rows = list(reader)
        columns = set(reader.fieldnames or [])

    errors: list[str] = []
    warnings: list[str] = []
    missing_columns = sorted(REQUIRED_COLUMNS - columns)
    if missing_columns:
        errors.append(f"missing required columns: {missing_columns}")

    source_ids: set[str] = set()
    for row_no, row in enumerate(rows, start=2):
        source_id = (row.get("source_id") or "").strip()
        status = (row.get("status") or "").strip()
        if not source_id:
            errors.append(f"row {row_no}: missing source_id")
            continue
        if source_id in source_ids:
            errors.append(f"row {row_no}: duplicate source_id {source_id}")
        source_ids.add(source_id)

        if status in EXECUTED_STATUSES:
            for field in ("execution_date_local", "timezone", "displayed_hit_count", "exported_record_count", "raw_export_filename", "raw_export_format", "executor"):
                if not (row.get(field) or "").strip():
                    errors.append(f"{source_id}: status={status} but missing {field}")
            if not (row.get("raw_export_sha256") or "").strip():
                warnings.append(f"{source_id}: executed source lacks raw_export_sha256 in manifest; populate from preserved artifact/checksum record")

        if status in PREPARED_STATUSES:
            for field in ("displayed_hit_count", "exported_record_count", "raw_export_filename", "raw_export_sha256"):
                if (row.get(field) or "").strip():
                    errors.append(f"{source_id}: prepared/pending source unexpectedly contains formal execution field {field}")

        if status == "manual_export_required" and source_id not in {"LILACS", "SCIELO"}:
            warnings.append(f"{source_id}: manual_export_required status should be justified explicitly")

    output = {
        "manifest_rows": len(rows),
        "source_ids": sorted(source_ids),
        "errors": errors,
        "warnings": warnings,
        "pass": not errors,
        "human_eligibility_decisions_created": 0,
        "prisma_decisions_created": 0,
    }
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(output, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(output, ensure_ascii=False, indent=2))
    if errors:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
