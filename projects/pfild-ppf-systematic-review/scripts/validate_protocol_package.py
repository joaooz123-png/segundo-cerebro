from __future__ import annotations

import hashlib
import json
import re
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
METHODS = ROOT / "methods"
OUT = ROOT / "artifacts" / "protocol_validation"
OUT.mkdir(parents=True, exist_ok=True)

FILES = {
    "protocol": METHODS / "PROTOCOL_V2.md",
    "addendum": METHODS / "PROTOCOL_V2_NORMATIVE_ADDENDUM.md",
    "screening_manual": METHODS / "MANUAL_TRIAGEM_V1_PT.md",
    "registration": METHODS / "OSF_REGISTRATION_PACKAGE.md",
    "amendments": METHODS / "AMENDMENT_LOG_V2.md",
    "adversarial_review": METHODS / "PROTOCOL_INTERNAL_ADVERSARIAL_REVIEW.md",
}

REQUIRED_PROTOCOL_HEADINGS = [
    "Transparency statement on protocol timing",
    "Review architecture",
    "Units of management",
    "Eligibility for the evidence census",
    "Information sources",
    "Record management and deduplication",
    "Selection process",
    "Risk of bias and appraisal",
    "Synthesis",
    "Certainty of evidence",
    "Deviations and amendments",
]

REQUIRED_SAFEGUARDS = {
    "no automated eligibility": [
        r"Automated methods must not make final inclusion or exclusion decisions",
        r"não decide inclusão ou exclusão",
    ],
    "no DOI-only merge": [r"must not be merged automatically", r"sharing only a DOI"],
    "preprint distinction": [r"preprint and journal publication"],
    "protocol timing disclosure": [r"human title/abstract eligibility decisions"],
    "dual screening": [r"Two reviewers will independently"],
    "no language restriction": [r"no language restriction"],
    "context control": [r"Contextual inclusion requires all three"],
    "citation saturation": [r"complete cycle yields no new direct-layer eligible report"],
    "AI provenance": [r"input dataset checksum", r"human-review status"],
}

PROHIBITED_CLAIMS = [
    r"PRISMA[- ]certified",
    r"PRISMA[- ]approved",
    r"fully prospective protocol",
    r"AI final eligibility decision",
    r"deduplicate by DOI alone",
]


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> None:
    failures: list[str] = []
    warnings: list[str] = []
    texts: dict[str, str] = {}
    manifest = {}

    for name, path in FILES.items():
        if not path.exists():
            failures.append(f"missing required file: {path.relative_to(ROOT)}")
            continue
        text = path.read_text(encoding="utf-8")
        texts[name] = text
        manifest[name] = {
            "path": str(path.relative_to(ROOT)),
            "bytes": path.stat().st_size,
            "sha256": sha256(path),
        }

    protocol = texts.get("protocol", "")
    for heading in REQUIRED_PROTOCOL_HEADINGS:
        if not re.search(rf"^##+\s+.*{re.escape(heading)}", protocol, re.I | re.M):
            failures.append(f"protocol heading missing: {heading}")

    combined = "\n".join(texts.values())
    for safeguard, patterns in REQUIRED_SAFEGUARDS.items():
        if not all(re.search(pattern, combined, re.I) for pattern in patterns):
            failures.append(f"required safeguard not demonstrated: {safeguard}")

    for pattern in PROHIBITED_CLAIMS:
        if re.search(pattern, combined, re.I):
            failures.append(f"prohibited or misleading claim detected: {pattern}")

    registration = texts.get("registration", "").lower()
    timing_patterns = [
        r"completed before registration.*search",
        r"prospective for human selection and analysis but not for initial search development or retrieval",
        r"search development.*preceded registration",
    ]
    if not any(re.search(pattern, registration, re.I | re.S) for pattern in timing_patterns):
        failures.append("OSF package lacks an explicit disclosure that search development/retrieval preceded registration")

    if not re.search(r"AMD-\d{3}", texts.get("amendments", "")):
        failures.append("amendment log has no structured amendment identifiers")

    result = {
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "status": "pass" if not failures else "fail",
        "failures": failures,
        "warnings": warnings,
        "manifest": manifest,
        "human_approval_status": "pending",
        "external_registration_status": "pending",
        "press_status": "pending",
    }
    (OUT / "protocol_validation.json").write_text(json.dumps(result, indent=2), encoding="utf-8")
    (OUT / "protocol_manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    print(json.dumps(result, indent=2))
    if failures:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
