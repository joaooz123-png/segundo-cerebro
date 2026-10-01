from __future__ import annotations

import json
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen

from bs4 import BeautifulSoup

OUT = Path(__file__).resolve().parents[1] / "artifacts" / "regional_probe"
OUT.mkdir(parents=True, exist_ok=True)

UA = "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 Chrome/139 Safari/537.36"

WEB_SOURCES = {
    "bvs_web": (
        "https://pesquisa.bvsalud.org/portal/",
        {
            "output": "site",
            "lang": "en",
            "from": "0",
            "sort": "",
            "format": "summary",
            "count": "50",
            "fb": "",
            "page": "1",
            "q": '"progressive pulmonary fibrosis"',
        },
    ),
    "scielo_web": (
        "https://search.scielo.org/",
        {
            "q": '"progressive pulmonary fibrosis"',
            "lang": "en",
            "count": "50",
            "from": "0",
            "output": "site",
            "sort": "",
            "format": "summary",
            "fb": "",
            "page": "1",
        },
    ),
}

ARTICLEMETA = (
    "https://articlemeta.scielo.org/api/v1/articles",
    {
        "from": "2026-01-01",
        "until": "2026-12-31",
        "limit": "1",
        "offset": "0",
        "body": "false",
    },
)


def fetch(url: str, accept: str = "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8") -> tuple[bytes, dict[str, str], int, str]:
    req = Request(
        url,
        headers={
            "User-Agent": UA,
            "Accept": accept,
            "Accept-Language": "en-US,en;q=0.9,pt-BR;q=0.8,es;q=0.7",
            "Cache-Control": "no-cache",
            "Pragma": "no-cache",
        },
    )
    with urlopen(req, timeout=90) as resp:
        return resp.read(), dict(resp.headers), resp.status, resp.geturl()


def summarize_html(name: str, html: str, url: str, status: int) -> dict:
    soup = BeautifulSoup(html, "html.parser")
    anchors = []
    for a in soup.find_all("a", href=True):
        text = " ".join(a.stripped_strings)
        href = a.get("href", "")
        if text or href:
            anchors.append({"text": text[:300], "href": href[:1000]})
    if name == "bvs_web":
        candidates = [a for a in anchors if "/resource/" in a["href"]]
    else:
        candidates = [
            a for a in anchors
            if "scielo.php?script=sci_arttext" in a["href"]
            or "scielo.br/j/" in a["href"]
            or "scielo.org.mx/scielo.php" in a["href"]
            or "scielo.cl/scielo.php" in a["href"]
            or "scielo.php?pid=" in a["href"]
        ]
    return {
        "name": name,
        "status": status,
        "url": url,
        "title": soup.title.get_text(" ", strip=True) if soup.title else "",
        "text_head": soup.get_text(" ", strip=True)[:5000],
        "anchors_total": len(anchors),
        "candidate_links": candidates[:100],
        "candidate_count": len(candidates),
        "class_samples": sorted({" ".join(x.get("class", [])) for x in soup.find_all(True) if x.get("class")})[:300],
    }


def probe_web_source(name: str, base: str, params: dict[str, str]) -> dict:
    requested = base + "?" + urlencode(params)
    try:
        body, headers, status, final_url = fetch(requested)
        html = body.decode(headers.get("Content-Type", "utf-8").split("charset=")[-1] if "charset=" in headers.get("Content-Type", "") else "utf-8", errors="replace")
        (OUT / f"{name}_first_page.html").write_text(html, encoding="utf-8")
        summary = summarize_html(name, html, final_url, status)
        summary["requested_url"] = requested
        summary["headers"] = {k: v for k, v in headers.items() if k.lower() in {"content-type", "content-length", "server", "date"}}
        return summary
    except HTTPError as exc:
        body = exc.read().decode("utf-8", errors="replace") if exc.fp else ""
        (OUT / f"{name}_http_error_{exc.code}.html").write_text(body, encoding="utf-8")
        return {
            "name": name,
            "requested_url": requested,
            "error": "HTTPError",
            "status": exc.code,
            "reason": str(exc.reason),
            "body_head": body[:3000],
        }
    except (URLError, TimeoutError) as exc:
        return {
            "name": name,
            "requested_url": requested,
            "error": type(exc).__name__,
            "reason": repr(exc),
        }


def probe_articlemeta() -> dict:
    base, params = ARTICLEMETA
    requested = base + "?" + urlencode(params)
    try:
        body, headers, status, final_url = fetch(requested, accept="application/json,*/*;q=0.8")
        text = body.decode("utf-8", errors="replace")
        (OUT / "scielo_articlemeta_probe.json").write_text(text, encoding="utf-8")
        payload = json.loads(text)
        objects = payload.get("objects", []) if isinstance(payload, dict) else []
        first = objects[0] if objects else None
        return {
            "name": "scielo_articlemeta",
            "status": status,
            "requested_url": requested,
            "final_url": final_url,
            "meta": payload.get("meta", {}) if isinstance(payload, dict) else {},
            "objects_count": len(objects),
            "first_object_keys": sorted(first.keys()) if isinstance(first, dict) else [],
            "first_object": first,
            "headers": {k: v for k, v in headers.items() if k.lower() in {"content-type", "content-length", "server", "date"}},
        }
    except HTTPError as exc:
        body = exc.read().decode("utf-8", errors="replace") if exc.fp else ""
        (OUT / f"scielo_articlemeta_http_error_{exc.code}.txt").write_text(body, encoding="utf-8")
        return {
            "name": "scielo_articlemeta",
            "requested_url": requested,
            "error": "HTTPError",
            "status": exc.code,
            "reason": str(exc.reason),
            "body_head": body[:3000],
        }
    except (URLError, TimeoutError, json.JSONDecodeError) as exc:
        return {
            "name": "scielo_articlemeta",
            "requested_url": requested,
            "error": type(exc).__name__,
            "reason": repr(exc),
        }


def main() -> None:
    result = {}
    for name, (base, params) in WEB_SOURCES.items():
        result[name] = probe_web_source(name, base, params)
    result["scielo_articlemeta"] = probe_articlemeta()
    (OUT / "regional_probe_summary.json").write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(result, ensure_ascii=False, indent=2))
    if result["scielo_articlemeta"].get("error") or result["scielo_articlemeta"].get("objects_count", 0) < 1:
        raise SystemExit("SciELO ArticleMeta probe failed; see artifact")


if __name__ == "__main__":
    main()
