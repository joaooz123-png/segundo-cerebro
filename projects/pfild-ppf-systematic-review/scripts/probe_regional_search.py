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

SOURCES = {
    "bvs": (
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
    "scielo": (
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


def fetch(url: str) -> tuple[str, dict[str, str], int, str]:
    req = Request(
        url,
        headers={
            "User-Agent": UA,
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.9,pt-BR;q=0.8,es;q=0.7",
            "Cache-Control": "no-cache",
            "Pragma": "no-cache",
        },
    )
    with urlopen(req, timeout=90) as resp:
        body = resp.read()
        return body.decode(resp.headers.get_content_charset() or "utf-8", errors="replace"), dict(resp.headers), resp.status, resp.geturl()


def summarize(name: str, html: str, url: str, status: int) -> dict:
    soup = BeautifulSoup(html, "html.parser")
    anchors = []
    for a in soup.find_all("a", href=True):
        text = " ".join(a.stripped_strings)
        href = a.get("href", "")
        if text or href:
            anchors.append({"text": text[:300], "href": href[:1000]})
    if name == "bvs":
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


def main() -> None:
    result = {}
    for name, (base, params) in SOURCES.items():
        requested = base + "?" + urlencode(params)
        try:
            html, headers, status, final_url = fetch(requested)
            (OUT / f"{name}_first_page.html").write_text(html, encoding="utf-8")
            summary = summarize(name, html, final_url, status)
            summary["requested_url"] = requested
            summary["headers"] = {k: v for k, v in headers.items() if k.lower() in {"content-type", "content-length", "server", "date"}}
            result[name] = summary
        except HTTPError as exc:
            body = exc.read().decode("utf-8", errors="replace") if exc.fp else ""
            (OUT / f"{name}_http_error_{exc.code}.html").write_text(body, encoding="utf-8")
            result[name] = {
                "name": name,
                "requested_url": requested,
                "error": "HTTPError",
                "status": exc.code,
                "reason": str(exc.reason),
                "body_head": body[:3000],
            }
        except (URLError, TimeoutError) as exc:
            result[name] = {
                "name": name,
                "requested_url": requested,
                "error": type(exc).__name__,
                "reason": repr(exc),
            }
    (OUT / "regional_probe_summary.json").write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(result, ensure_ascii=False, indent=2))
    if not result.get("scielo") or result["scielo"].get("error"):
        raise SystemExit("SciELO probe failed; see artifact")


if __name__ == "__main__":
    main()
