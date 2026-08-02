from __future__ import annotations
import base64, hashlib
from pathlib import Path

ROOT = Path(__file__).resolve().parent
PARTS = sorted((ROOT / "workbook_chunks").glob("workbook.b64.part-*"))
TARGET = ROOT / "PFILD_PPF_censo_bibliografico_formal_v3_pubmed.xlsx"
EXPECTED_SHA256 = "2c76d373f696b2c84990c3f5d66e1ea6f70562151c4ad9d2c0b4f60762511f14"

if not PARTS:
    raise FileNotFoundError("No workbook chunks found")
payload = "".join(p.read_text(encoding="ascii") for p in PARTS)
TARGET.write_bytes(base64.b64decode(payload))
actual = hashlib.sha256(TARGET.read_bytes()).hexdigest()
if actual != EXPECTED_SHA256:
    raise RuntimeError(f"Checksum mismatch: {actual}")
print(f"Restored {TARGET.name}: {TARGET.stat().st_size} bytes; sha256={actual}")
