from __future__ import annotations

import json
from pathlib import Path
from urllib.parse import urlencode
from urllib.request import Request, urlopen

from bs4 import BeautifulSoup

OUT = Path(__file__).resolve().parents[1] / "artifacts" / "regional_probe"
OUT.mkdir(parents=True, exist_ok=True)

UA = "pfild_ppf_systematic_review/2.0 (+https://github.com/joaooz123-png/segundo-cerebro)"

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
    req = Request(url, headers={"User-Agent": UA, "Accept": "text/html,application/xhtml+xml"})
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
    candidates = []
    if name == "bvs":
        candidates = [a for a in anchors if "/resource/" in a["href"]]
    else:
        candidates = [
            a for a in anchors
            if "scielo.php?script=sci_arttext" in a["href"]
            or "scielo.br/j/" in a["href"]
            or "scielo.org.mx/scielo.php" in a["href"]
            or "scielo.cl/scielo.php" in a["href"]
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
        html, headers, status, final_url = fetch(requested)
        (OUT / f"{name}_first_page.html").write_text(html, encoding="utf-8")
        summary = summarize(name, html, final_url, status)
        summary["requested_url"] = requested
        summary["headers"] = {k: v for k, v in headers.items() if k.lower() in {"content-type", "content-length", "server", "date"}}
        result[name] = summary
    (OUT / "regional_probe_summary.json").write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
