from __future__ import annotations

import json
import os
import urllib.parse
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = Path(os.getenv("PFILD_REGIONAL_PROBE_DIR", ROOT / "artifacts" / "regional_probe"))
OUT.mkdir(parents=True, exist_ok=True)

BVS_QUERY = 'tw:"progressive pulmonary fibrosis" OR tw:"progressive fibrosing interstitial lung disease" OR tw:"progressive fibrotic interstitial lung disease" OR tw:"fibrose pulmonar progressiva" OR tw:"fibrosis pulmonar progresiva"'
SCIELO_QUERY = 'subject:("progressive pulmonary fibrosis" OR "progressive fibrosing interstitial lung disease" OR "progressive fibrotic interstitial lung disease" OR "fibrose pulmonar progressiva" OR "fibrosis pulmonar progresiva")'

URLS = {
    "bvs_html": "https://pesquisa.bvsalud.org/portal/?" + urllib.parse.urlencode({
        "output": "site", "lang": "pt", "from": "0", "sort": "", "format": "summary",
        "count": "50", "page": "1", "q": BVS_QUERY,
    }),
    "bvs_json_guess": "https://pesquisa.bvsalud.org/portal/?" + urllib.parse.urlencode({
        "output": "site", "lang": "pt", "from": "0", "sort": "", "format": "json",
        "count": "50", "page": "1", "q": BVS_QUERY,
    }),
    "scielo_html": "https://search.scielo.org/?" + urllib.parse.urlencode({
        "q": SCIELO_QUERY, "lang": "en", "count": "50", "from": "0",
    }),
    "scielo_csv_guess": "https://search.scielo.org/?" + urllib.parse.urlencode({
        "q": SCIELO_QUERY, "lang": "en", "count": "50", "from": "0", "format": "csv",
    }),
}


def fetch(name: str, url: str) -> dict:
    req = urllib.request.Request(url, headers={
        "User-Agent": "pfild-ppf-systematic-review/1.0 (+https://github.com/joaooz123-png/segundo-cerebro)",
        "Accept": "text/html,application/json,text/csv;q=0.9,*/*;q=0.8",
    })
    with urllib.request.urlopen(req, timeout=120) as resp:
        raw = resp.read()
        headers = dict(resp.headers.items())
        status = getattr(resp, "status", 200)
        final_url = resp.geturl()
    suffix = ".bin"
    ctype = headers.get("Content-Type", "").lower()
    if "html" in ctype:
        suffix = ".html"
    elif "json" in ctype:
        suffix = ".json"
    elif "csv" in ctype:
        suffix = ".csv"
    (OUT / f"{name}{suffix}").write_bytes(raw)
    text = raw[:1500].decode("utf-8", errors="replace")
    return {
        "name": name,
        "requested_url": url,
        "final_url": final_url,
        "status": status,
        "content_type": headers.get("Content-Type", ""),
        "content_length": len(raw),
        "preview": text,
    }


results = []
for name, url in URLS.items():
    try:
        results.append(fetch(name, url))
    except Exception as exc:
        results.append({"name": name, "requested_url": url, "error": repr(exc)})

(OUT / "probe_summary.json").write_text(json.dumps({
    "bvs_query": BVS_QUERY,
    "scielo_query": SCIELO_QUERY,
    "results": results,
}, ensure_ascii=False, indent=2), encoding="utf-8")

print(json.dumps(results, ensure_ascii=False, indent=2))
