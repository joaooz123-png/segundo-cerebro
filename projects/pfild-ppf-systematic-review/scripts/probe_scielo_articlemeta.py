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
HOST = "https://articlemeta.scielo.org"
USER_AGENT = "pfild_ppf_systematic_review/1.6 (+https://github.com/joaooz123-png/segundo-cerebro)"

TESTS = {
    "article_baseline": ("/api/v1/article", {"limit": "5", "format": "json"}),
    "articles_baseline": ("/api/v1/articles", {"limit": "5", "fmt": "xylose"}),
    "article_query_ppf": ("/api/v1/article", {"q": "progressive pulmonary fibrosis", "limit": "100", "format": "json"}),
    "articles_query_ppf": ("/api/v1/articles", {"q": "progressive pulmonary fibrosis", "limit": "100", "fmt": "xylose"}),
    "article_query_pfild": ("/api/v1/article", {"q": "progressive fibrosing interstitial lung disease", "limit": "100", "format": "json"}),
    "article_query_portuguese": ("/api/v1/article", {"q": "fibrose pulmonar progressiva", "limit": "100", "format": "json"}),
    "article_query_spanish": ("/api/v1/article", {"q": "fibrosis pulmonar progresiva", "limit": "100", "format": "json"}),
    "article_subject_parameter": ("/api/v1/article", {"subject": "progressive pulmonary fibrosis", "limit": "100", "format": "json"}),
    "article_identifiers_scl": ("/api/v1/article/identifiers", {"collection": "scl", "limit": "5", "offset": "0"}),
}


def request(endpoint: str, params: dict[str, str], name: str) -> dict:
    url = HOST + endpoint + "?" + urllib.parse.urlencode(params)
    req = urllib.request.Request(
        url,
        headers={
            "User-Agent": USER_AGENT,
            "Accept": "application/json,application/xml;q=0.9,*/*;q=0.8",
        },
    )
    with urllib.request.urlopen(req, timeout=120) as response:
        raw = response.read()
        result = {
            "endpoint": endpoint,
            "params": params,
            "request_url": url,
            "final_url": response.geturl(),
            "status": response.status,
            "content_type": response.headers.get("Content-Type", ""),
            "sha256": hashlib.sha256(raw).hexdigest(),
            "size_bytes": len(raw),
        }
        path = OUT / f"{name}.raw"
        path.write_bytes(raw)
        result["raw_file"] = path.name
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
                            if key == "meta":
                                result["meta"] = value
                        else:
                            result[key] = value
                objects = data.get("objects")
                if isinstance(objects, list) and objects:
                    result["first_object_keys"] = sorted(objects[0].keys()) if isinstance(objects[0], dict) else []
                    result["first_object_preview"] = objects[0]
            elif isinstance(data, list):
                result["list_length"] = len(data)
                if data:
                    result["first_item_preview"] = data[0]
        except Exception as exc:
            result["parse_error"] = repr(exc)
        return result


def main() -> None:
    results = {}
    for name, (endpoint, params) in TESTS.items():
        try:
            results[name] = request(endpoint, params, name)
        except Exception as exc:
            results[name] = {"endpoint": endpoint, "params": params, "error": repr(exc)}
    summary = {
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "host": HOST,
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
