from __future__ import annotations

import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SEARCH_DIR = ROOT / "search" / "subscription"
FILES = {
    "embase.com": SEARCH_DIR / "embase_com_v1.txt",
    "scopus": SEARCH_DIR / "scopus_v1.txt",
    "web_of_science": SEARCH_DIR / "web_of_science_v1.txt",
    "cinahl_ebsco": SEARCH_DIR / "cinahl_ebsco_v1.txt",
    "central": SEARCH_DIR / "central_v1.txt",
}

REQUIRED_CONCEPTS = {
    "explicit_pfild": [r"pf-ild", r"\bpfild\b"],
    "ppf_phrase": [r"progressive pulmonary fibrosis"],
    "fibrosing_ild": [r"fibrosing interstitial lung disease", r"fibrotic interstitial lung disease"],
    "progression": [r"\bprogression\b", r"\bprogressive\b"],
}

FORBIDDEN_LIMIT_PATTERNS = [
    r"english language",
    r"\[english\]",
    r"language\s*=\s*english",
    r"human\s+only",
    r"humans?\s+only",
    r"publication\s+year\s*[:=]",
    r"document\s+type\s*[:=]",
    r"conference abstract.*not",
]

PLATFORM_MARKERS = {
    "embase.com": [r":ti", r":ab", r":kw", r"/exp"],
    "scopus": [r"title-abs-key"],
    "web_of_science": [r"ts=", r"ti="],
    "cinahl_ebsco": [r"\bti\b", r"\bab\b", r"\bmh\b"],
    "central": [r":ti,ab,kw", r"mesh descriptor"],
}


def check_file(name: str, path: Path) -> dict:
    if not path.exists():
        return {"database": name, "path": str(path), "status": "FAIL", "errors": ["missing file"]}
    text = path.read_text(encoding="utf-8")
    low = text.casefold()
    errors: list[str] = []
    warnings: list[str] = []

    for concept, patterns in REQUIRED_CONCEPTS.items():
        if not any(re.search(pattern, low, re.I) for pattern in patterns):
            errors.append(f"missing required concept: {concept}")

    if "progressive pulmonary fibrosis" in low:
        if name != "central" and not any(token in low for token in ["title", ":ti", "ti=(", "ti \""]):
            warnings.append("PPF phrase present but title/context protection is not obvious from static audit")

    for pattern in FORBIDDEN_LIMIT_PATTERNS:
        if re.search(pattern, low, re.I):
            # Comments describing prohibited limits are acceptable; flag for manual review instead of hard failure.
            warnings.append(f"possible forbidden limiter text detected: {pattern}")

    for marker in PLATFORM_MARKERS[name]:
        if not re.search(marker, low, re.I):
            errors.append(f"missing expected platform syntax marker: {marker}")

    if "no language" not in low and "no date" not in low:
        warnings.append("explicit no-limit governance statement not found")

    status = "PASS" if not errors else "FAIL"
    return {
        "database": name,
        "path": str(path.relative_to(ROOT)),
        "status": status,
        "errors": errors,
        "warnings": warnings,
        "human_eligibility_decisions_created": 0,
        "prisma_decisions_created": 0,
    }


def main() -> None:
    results = [check_file(name, path) for name, path in FILES.items()]
    output = {
        "translation_files": len(results),
        "pass": sum(r["status"] == "PASS" for r in results),
        "fail": sum(r["status"] == "FAIL" for r in results),
        "results": results,
        "human_eligibility_decisions_created": 0,
        "prisma_decisions_created": 0,
    }
    out_path = ROOT / "artifacts" / "database_translation_validation.json"
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(output, indent=2, ensure_ascii=False), encoding="utf-8")
    print(json.dumps(output, indent=2, ensure_ascii=False))
    if output["fail"]:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
