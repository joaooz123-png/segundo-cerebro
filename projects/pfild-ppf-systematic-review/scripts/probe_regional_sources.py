from __future__ import annotations

import hashlib
import json
import re
import time
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from html.parser import HTMLParser
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "artifacts" / "regional_sources_probe"
OUT.mkdir(parents=True, exist_ok=True)

USER_AGENT = "pfild_ppf_systematic_review/1.4 (+https://github.com/joaooz123-png/segundo-cerebro)"

TERM_BLOCK = (
    '"progressive pulmonary fibrosis" OR '
    '"progressive fibrosing interstitial lung disease" OR '
    '"progressive-fibrosing interstitial lung disease" OR '
    '"progressive fibrotic interstitial lung disease" OR '
    '"fibrose pulmonar progressiva" OR '
    '"doença pulmonar intersticial fibrosante progressiva" OR '
    '"fibrosis pulmonar progresiva" OR '
    '"enfermedad pulmonar intersticial fibrosante progresiva" OR '
    '"PF-ILD" OR PFILD'
)

SOURCES = {
    "scielo": {
        "base": "https://search.scielo.org/",
        "params": {
            "q": f"subject:({TERM_BLOCK})",
            "lang": "en",
            "count": "100",
            "from": "0",
            "sort": "",
            "format": "summary",
            "page": "1",
        },
    },
    "bvs": {
        "base": "https://pesquisa.bvsalud.org/portal/",
        "params": {
            "q": f"tw:({TERM_BLOCK})",
            "lang": "pt",
            "output": "site",
            "count": "100",
            "from": "0",
            "sort": "",
            "format": "summary",
            "page": "1",
        },
    },
    "lilacs": {
        "base": "https://pesquisa.bvsalud.org/portal/",
        "params": {
            "q": f"tw:({TERM_BLOCK})",
            "lang": "pt",
            "output": "site",
            "count": "100",
            "from": "0",
            "sort": "",
            "format": "summary",
            "page": "1",
            "filter[db][]": "LILACS",
        },
    },
}


class FormInspector(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.forms: list[dict[str, Any]] = []
        self.links: list[dict[str, str]] = []
        self.scripts: list[str] = []
        self.current_form: dict[str, Any] | None = None
        self.in_script = False
        self.script_buffer: list[str] = []

    @staticmethod
    def attrs_dict(attrs: list[tuple[str, str | None]]) -> dict[str, str]:
        return {key: value or "" for key, value in attrs}

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        data = self.attrs_dict(attrs)
        if tag == "form":
            self.current_form = {
                "action": data.get("action", ""),
                "method": data.get("method", "get").lower(),
                "id": data.get("id", ""),
                "class": data.get("class", ""),
                "controls": [],
            }
            self.forms.append(self.current_form)
        elif tag in {"input", "button", "select", "textarea"} and self.current_form is not None:
            self.current_form["controls"].append({"tag": tag, **data})
        elif tag == "a":
            href = data.get("href", "")
            if href:
                self.links.append({
                    "href": href,
                    "id": data.get("id", ""),
                    "class": data.get("class", ""),
                    "title": data.get("title", ""),
                })
        elif tag == "script":
            src = data.get("src", "")
            if src:
                self.scripts.append(src)
            self.in_script = True
            self.script_buffer = []

    def handle_endtag(self, tag: str) -> None:
        if tag == "form":
            self.current_form = None
        elif tag == "script":
            if self.script_buffer:
                self.scripts.append("".join(self.script_buffer))
            self.in_script = False
            self.script_buffer = []

    def handle_data(self, data: str) -> None:
        if self.in_script:
            self.script_buffer.append(data)


def fetch(url: str, method: str = "GET", payload: dict[str, str] | None = None) -> dict[str, Any]:
    body = None
    headers = {
        "User-Agent": USER_AGENT,
        "Accept": "text/html,application/xhtml+xml,application/xml,text/csv,application/x-research-info-systems,*/*;q=0.8",
        "Accept-Language": "en,pt-BR;q=0.9,es;q=0.8",
    }
    if payload is not None:
        body = urllib.parse.urlencode(payload, doseq=True).encode("utf-8")
        headers["Content-Type"] = "application/x-www-form-urlencoded"
    request = urllib.request.Request(url, data=body, headers=headers, method=method)
    with urllib.request.urlopen(request, timeout=120) as response:
        raw = response.read()
        return {
            "request_url": url,
            "final_url": response.geturl(),
            "status": response.status,
            "headers": dict(response.headers.items()),
            "raw": raw,
            "sha256": hashlib.sha256(raw).hexdigest(),
        }


def relevant(value: str) -> bool:
    return bool(re.search(r"export|download|ris|csv|bibtex|citation|send_result|format", value or "", re.I))


def save_json(path: Path, value: Any) -> None:
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2), encoding="utf-8")


def probe_source(name: str, config: dict[str, Any]) -> dict[str, Any]:
    url = config["base"] + "?" + urllib.parse.urlencode(config["params"], doseq=True)
    response = fetch(url)
    raw = response.pop("raw")
    html_path = OUT / f"{name}_search.html"
    html_path.write_bytes(raw)
    text = raw.decode("utf-8", errors="replace")

    parser = FormInspector()
    parser.feed(text)

    forms = parser.forms
    relevant_forms = []
    for index, form in enumerate(forms):
        signature = " ".join([
            form.get("action", ""), form.get("id", ""), form.get("class", ""),
            " ".join(" ".join(str(v) for v in control.values()) for control in form.get("controls", [])),
        ])
        if relevant(signature):
            relevant_forms.append({"form_index": index, **form})

    relevant_links = [link for link in parser.links if relevant(" ".join(link.values()))]
    relevant_scripts = [script for script in parser.scripts if relevant(script)]

    snippets = []
    for match in re.finditer(r".{0,300}(?:export|download|RIS|CSV|BibTeX|citation).{0,500}", text, flags=re.I | re.S):
        snippets.append(re.sub(r"\s+", " ", match.group(0))[:1000])
        if len(snippets) >= 40:
            break

    save_json(OUT / f"{name}_forms.json", forms)
    save_json(OUT / f"{name}_relevant_forms.json", relevant_forms)
    save_json(OUT / f"{name}_relevant_links.json", relevant_links)
    save_json(OUT / f"{name}_relevant_scripts.json", relevant_scripts)
    save_json(OUT / f"{name}_export_snippets.json", snippets)

    # Save external JavaScript files that appear export-related.
    downloaded_scripts = []
    for idx, script in enumerate(parser.scripts):
        if not script.startswith(("http://", "https://", "/")):
            continue
        absolute = urllib.parse.urljoin(response["final_url"], script)
        if not relevant(absolute) and idx > 20:
            continue
        try:
            script_response = fetch(absolute)
            script_raw = script_response.pop("raw")
            script_path = OUT / f"{name}_script_{idx:03d}.js"
            script_path.write_bytes(script_raw)
            downloaded_scripts.append({"path": script_path.name, **script_response})
        except Exception as exc:
            downloaded_scripts.append({"url": absolute, "error": repr(exc)})
        time.sleep(0.15)

    return {
        "source": name,
        "query_url": url,
        "query": config["params"]["q"],
        "response": response,
        "html_file": html_path.name,
        "form_count": len(forms),
        "relevant_form_count": len(relevant_forms),
        "relevant_link_count": len(relevant_links),
        "relevant_script_count": len(relevant_scripts),
        "downloaded_scripts": downloaded_scripts,
    }


def main() -> None:
    results = []
    for name, config in SOURCES.items():
        try:
            results.append(probe_source(name, config))
        except Exception as exc:
            results.append({"source": name, "error": repr(exc)})
        time.sleep(0.5)
    summary = {
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "purpose": "technical discovery of reproducible official export routes",
        "term_block": TERM_BLOCK,
        "sources": results,
        "eligibility_decisions_created": 0,
        "prisma_counts_changed": 0,
    }
    save_json(OUT / "regional_sources_probe_summary.json", summary)
    print(json.dumps(summary, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
