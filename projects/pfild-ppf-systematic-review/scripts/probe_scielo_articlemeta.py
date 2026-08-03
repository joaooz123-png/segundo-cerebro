from __future__ import annotations

import hashlib
import json
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "artifacts" / "scielo_articlemeta_probe"
OUT.mkdir(parents=True, exist_ok=True)
BASE = "https://articlemeta.scielo.org/api/v1/article/"
USER_AGENT = "pfild_ppf_systematic_review/1.5 (+https://github.com/joaooz123-png/segundo-cerebro)"

TESTS = {
    "baseline": {"limit": "5", "format": "json"},
    "query_ppf": {"q": "progressive pulmonary fibrosis", "limit": "100", "format": "json"},
    "query_pfild": {"q": "progressive fibrosing interstitial lung disease", "limit": "100", "format": "json"},
    "query_portuguese": {"q": "fibrose pulmonar progressiva", "limit": "100", "format": "json"},
    "query_spanish": {"q": "fibrosis pulmonar progresiva", "limit": "100", "format": "json"},
    "subject_parameter": {"subject": "progressive pulmonary fibrosis", "limit": "100", "format": "json"},
}


def request(params: dict[str, str]) -> dict:
    url = BASE + "?" + urllib.parse.urlencode(params)
    req = urllib.request.Request(
        url,
        headers={
            "User-Agent": USER_AGENT,
            "Accept": "application/json,application/xml;q=0.9,*/*;q=0.8",
        },
    )
    with urllib.request.urlopen(req, timeout=120) as response:
        raw = response.read()
        content_type = response.headers.get("Content-Type", "")
        result = {
            "request_url": url,
            "final_url": response.geturl(),
            "status": response.status,
            "content_type": content_type,
            "sha256": hashlib.sha256(raw).hexdigest(),
            "size_bytes": len(raw),
        }
        try:
            data = json.loads(raw.decode("utf-8"))
            result["json_type"] = type(data).__name__
            if isinstance(data, dict):
                result["top_level_keys"] = sorted(data.keys())
                for key in ("meta", "objects", "results", "docs", "count", "next", "previous"):
                    if key in data:
                        value = data[key]
                        if isinstance(value, list):
                            result[f"{key}_length"] = len(value)
                        elif isinstance(value, dict):
                            result[f"{key}_keys"] = sorted(value.keys())
                        else:
                            result[key] = value
            path = OUT / (urllib.parse.quote(params.get("q", params.get("subject", "baseline")), safe="")[:80] + ".json")
            path.write_bytes(raw)
            result["raw_file"] = path.name
        except Exception as exc:
            path = OUT / (urllib.parse.quote(params.get("q", params.get("subject", "baseline")), safe="")[:80] + ".bin")
            path.write_bytes(raw)
            result["raw_file"] = path.name
            result["parse_error"] = repr(exc)
        return result


def main() -> None:
    results = {}
    for name, params in TESTS.items():
        try:
            results[name] = request(params)
        except Exception as exc:
            results[name] = {"error": repr(exc)}
    summary = {
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "api": BASE,
        "tests": results,
        "eligibility_decisions_created": 0,
        "prisma_counts_changed": 0,
    }
    (OUT / "scielo_articlemeta_probe_summary.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    print(json.dumps(summary, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
