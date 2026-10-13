from __future__ import annotations

import csv
import gzip
import hashlib
import json
import os
import re
import time
import unicodedata
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from urllib.parse import urljoin, urlparse

import requests
from bs4 import BeautifulSoup

ROOT = Path(__file__).resolve().parents[1]
OUTPUT_DIR = Path(os.getenv("PFILD_BDTD_OUTPUT_DIR", ROOT / "artifacts" / "bdtd_theses"))
RAW_DIR = OUTPUT_DIR / "raw"
BASE_URL = "https://bdtd.ibict.br"
SEARCH_URL = BASE_URL + "/vufind/Search/Results"
USER_AGENT = "pfild-ppf-systematic-review/1.0 (+https://github.com/joaooz123-png/segundo-cerebro)"
REQUEST_DELAY = float(os.getenv("BDTD_REQUEST_DELAY", "0.60"))
MAX_RETRIES = 5
MAX_PAGES_PER_QUERY = int(os.getenv("BDTD_MAX_PAGES_PER_QUERY", "50"))

SEARCH_STRATA = [
    ("phrase_en_ppf", '"progressive pulmonary fibrosis"'),
    ("phrase_en_pfild", '"progressive fibrosing interstitial lung disease"'),
    ("phrase_en_pfild_plural", '"progressive fibrosing interstitial lung diseases"'),
    ("phrase_en_fibrotic", '"progressive fibrotic interstitial lung disease"'),
    ("phrase_en_ild", '"progressive fibrosing ILD"'),
    ("phrase_en_pf_ild", '"PF-ILD"'),
    ("phrase_en_pfild_acronym", "PFILD"),
    ("phrase_en_phenotype", '"progressive fibrotic phenotype"'),
    ("phrase_pt_ppf", '"fibrose pulmonar progressiva"'),
    ("phrase_pt_pfild", '"doença pulmonar intersticial fibrosante progressiva"'),
    ("phrase_pt_pfild_plural", '"doenças pulmonares intersticiais fibrosantes progressivas"'),
    ("phrase_pt_phenotype", '"fenótipo fibrosante progressivo"'),
    ("phrase_es_ppf", '"fibrosis pulmonar progresiva"'),
    ("phrase_es_pfild", '"enfermedad pulmonar intersticial fibrosante progresiva"'),
    ("phrase_es_pfild_plural", '"enfermedades pulmonares intersticiales fibrosantes progresivas"'),
    ("phrase_es_phenotype", '"fenotipo fibrosante progresivo"'),
    ("concept_pt", '"doença pulmonar intersticial" AND fibros* AND progress*'),
    ("concept_es", '"enfermedad pulmonar intersticial" AND fibros* AND progres*'),
    ("concept_en", '"interstitial lung disease" AND fibros* AND progress*'),
]

FIELDS = [
    "bdtd_record_id", "title", "authors", "advisors", "institution", "program",
    "document_type", "publication_year", "language", "subjects", "abstract",
    "doi", "source_url", "document_url", "search_strata", "exact_phrase_flag",
    "conceptual_flag", "machine_priority", "human_decision",
]

EXACT_TERMS = [
    "progressive pulmonary fibrosis",
    "progressive fibrosing interstitial lung disease",
    "progressive fibrosing interstitial lung diseases",
    "progressive fibrotic interstitial lung disease",
    "progressive fibrosing ild", "pf-ild", "pfild",
    "progressive fibrotic phenotype", "fibrose pulmonar progressiva",
    "doença pulmonar intersticial fibrosante progressiva",
    "doenças pulmonares intersticiais fibrosantes progressivas",
    "fenótipo fibrosante progressivo", "fibrosis pulmonar progresiva",
    "enfermedad pulmonar intersticial fibrosante progresiva",
    "enfermedades pulmonares intersticiales fibrosantes progresivas",
    "fenotipo fibrosante progresivo",
]


def normalize_space(value: str) -> str:
    return re.sub(r"\s+", " ", value or "").strip()


def strip_accents(value: str) -> str:
    return "".join(ch for ch in unicodedata.normalize("NFKD", value) if not unicodedata.combining(ch))


def norm(value: str) -> str:
    return strip_accents(normalize_space(value).casefold())


def sha256_bytes(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def request(session: requests.Session, url: str, params: dict[str, Any] | None = None) -> requests.Response:
    last: Exception | None = None
    for attempt in range(1, MAX_RETRIES + 1):
        try:
            response = session.get(url, params=params, timeout=120)
            if response.status_code == 429 or response.status_code >= 500:
                raise requests.HTTPError(f"HTTP {response.status_code}", response=response)
            response.raise_for_status()
            return response
        except Exception as exc:
            last = exc
            if attempt == MAX_RETRIES:
                raise
            time.sleep(min(30.0, 2 ** (attempt - 1)))
    assert last is not None
    raise last


def meta_values(soup: BeautifulSoup, names: list[str]) -> list[str]:
    values: list[str] = []
    lowered = {n.casefold() for n in names}
    for tag in soup.find_all("meta"):
        name = str(tag.get("name") or tag.get("property") or "").casefold()
        if name in lowered:
            value = normalize_space(str(tag.get("content") or ""))
            if value and value not in values:
                values.append(value)
    return values


def first_meta(soup: BeautifulSoup, names: list[str]) -> str:
    vals = meta_values(soup, names)
    return vals[0] if vals else ""


def record_links(html: bytes, final_url: str) -> list[str]:
    soup = BeautifulSoup(html, "lxml")
    seen: set[str] = set()
    links: list[str] = []
    for anchor in soup.find_all("a", href=True):
        href = urljoin(final_url, str(anchor.get("href")))
        parsed = urlparse(href)
        if parsed.netloc.casefold() not in {"bdtd.ibict.br", "www.bdtd.ibict.br"}:
            continue
        if "/Record/" not in parsed.path and "/vufind/Record/" not in parsed.path:
            continue
        clean = parsed._replace(query="", fragment="").geturl().rstrip("/")
        if clean not in seen:
            seen.add(clean)
            links.append(clean)
    return links


def record_id_from_url(url: str) -> str:
    path = urlparse(url).path.rstrip("/")
    return path.split("/")[-1] if path else hashlib.sha256(url.encode()).hexdigest()[:20]


def text_after_label(soup: BeautifulSoup, labels: list[str]) -> str:
    targets = {norm(x) for x in labels}
    for tag in soup.find_all(["dt", "th", "strong", "span", "div"]):
        label = norm(tag.get_text(" ", strip=True)).rstrip(":")
        if label in targets:
            sibling = tag.find_next_sibling()
            if sibling:
                value = normalize_space(sibling.get_text(" ", strip=True))
                if value:
                    return value
    return ""


def parse_record(html: bytes, url: str, strata: set[str]) -> dict[str, Any] | None:
    soup = BeautifulSoup(html, "lxml")
    title = first_meta(soup, ["citation_title", "dc.title", "DC.Title"])
    if not title:
        h = soup.find(["h1", "h2"], class_=re.compile("title|record", re.I))
        title = normalize_space(h.get_text(" ", strip=True)) if h else ""
    if not title:
        return None

    authors = meta_values(soup, ["citation_author", "dc.creator", "DC.Creator"])
    description = first_meta(soup, ["description", "dc.description", "DC.Description", "citation_abstract"])
    language = first_meta(soup, ["dc.language", "DC.Language", "citation_language"])
    date = first_meta(soup, ["citation_publication_date", "dc.date", "DC.Date"])
    year_match = re.search(r"\b(?:18|19|20)\d{2}\b", date or soup.get_text(" ", strip=True)[:3000])
    year = year_match.group(0) if year_match else ""
    subjects = meta_values(soup, ["dc.subject", "DC.Subject", "citation_keywords"])
    doi = first_meta(soup, ["citation_doi", "dc.identifier", "DC.Identifier"])
    doi_match = re.search(r"10\.\d{4,9}/[-._;()/:A-Z0-9]+", doi, re.I)
    doi = doi_match.group(0).rstrip(" .;,") if doi_match else ""

    institution = text_after_label(soup, ["Instituição de defesa", "Instituição", "Institution"])
    program = text_after_label(soup, ["Programa de Pós-Graduação", "Programa", "Program"])
    doc_type = text_after_label(soup, ["Tipo de documento", "Tipo", "Document Type"])
    advisors = text_after_label(soup, ["Orientador(a)", "Orientador", "Advisor"])

    document_url = ""
    for anchor in soup.find_all("a", href=True):
        label = norm(anchor.get_text(" ", strip=True))
        if any(x in label for x in ["acessar documento", "texto completo", "full text", "documento"]):
            document_url = urljoin(url, str(anchor.get("href")))
            break

    combined = norm(title + "\n" + description + "\n" + "; ".join(subjects))
    exact = any(norm(term) in combined for term in EXACT_TERMS)
    conceptual = (
        ("interstitial lung" in combined or "pulmonar intersticial" in combined)
        and "fibros" in combined
        and ("progress" in combined or "progres" in combined)
    )
    return {
        "bdtd_record_id": record_id_from_url(url),
        "title": title,
        "authors": "; ".join(authors),
        "advisors": advisors,
        "institution": institution,
        "program": program,
        "document_type": doc_type,
        "publication_year": year,
        "language": language,
        "subjects": "; ".join(subjects),
        "abstract": description,
        "doi": doi,
        "source_url": url,
        "document_url": document_url,
        "search_strata": "; ".join(sorted(strata)),
        "exact_phrase_flag": exact,
        "conceptual_flag": conceptual,
        "machine_priority": "high" if exact else "medium" if conceptual else "low",
        "human_decision": "not reviewed",
    }


def write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=FIELDS, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def write_json(path: Path, obj: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(obj, ensure_ascii=False, indent=2), encoding="utf-8")


def main() -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    RAW_DIR.mkdir(parents=True, exist_ok=True)
    session = requests.Session()
    session.headers.update({"User-Agent": USER_AGENT, "Accept-Language": "pt-BR,pt;q=0.9,en;q=0.8,es;q=0.7"})

    links_to_strata: defaultdict[str, set[str]] = defaultdict(set)
    trace: list[dict[str, Any]] = []
    status = "completed"
    blocking_error = ""

    for query_index, (stratum, query) in enumerate(SEARCH_STRATA, start=1):
        previous_signature = ""
        for page in range(1, MAX_PAGES_PER_QUERY + 1):
            params = {
                "lookfor": query,
                "type": "AllFields",
                "sort": "relevance",
                "limit": "100",
                "page": str(page),
            }
            try:
                response = request(session, SEARCH_URL, params=params)
            except requests.HTTPError as exc:
                code = exc.response.status_code if exc.response is not None else None
                status = f"blocked_http_{code}" if code else "request_failed"
                blocking_error = repr(exc)
                trace.append({"stratum": stratum, "query": query, "page": page, "status": status, "error": blocking_error})
                break
            except Exception as exc:
                status = "request_failed"
                blocking_error = repr(exc)
                trace.append({"stratum": stratum, "query": query, "page": page, "status": status, "error": blocking_error})
                break

            raw = response.content
            raw_path = RAW_DIR / f"search_{query_index:02d}_{page:03d}.html.gz"
            with gzip.open(raw_path, "wb") as handle:
                handle.write(raw)
            links = record_links(raw, response.url)
            signature = hashlib.sha256("\n".join(links).encode()).hexdigest()
            trace.append({
                "stratum": stratum, "query": query, "page": page, "record_links": len(links),
                "request_url": response.url, "raw_file": raw_path.name,
                "raw_sha256": sha256_bytes(raw), "http_status": response.status_code,
            })
            if not links or signature == previous_signature:
                break
            previous_signature = signature
            new_links = 0
            for link in links:
                if not links_to_strata[link]:
                    new_links += 1
                links_to_strata[link].add(stratum)
            if new_links == 0:
                break
            time.sleep(REQUEST_DELAY)
        if status != "completed":
            break

    records: list[dict[str, Any]] = []
    detail_failures: list[dict[str, str]] = []
    for idx, (link, strata) in enumerate(sorted(links_to_strata.items()), start=1):
        try:
            response = request(session, link)
            raw = response.content
            raw_path = RAW_DIR / f"record_{idx:04d}.html.gz"
            with gzip.open(raw_path, "wb") as handle:
                handle.write(raw)
            rec = parse_record(raw, response.url, strata)
            if rec:
                records.append(rec)
        except Exception as exc:
            detail_failures.append({"url": link, "error": repr(exc)})
        time.sleep(REQUEST_DELAY)

    # Exact within-source source-representation dedup by BDTD record id.
    unique: dict[str, dict[str, Any]] = {}
    for row in records:
        rid = row["bdtd_record_id"]
        if rid not in unique:
            unique[rid] = row
    rows = sorted(unique.values(), key=lambda r: (
        r["machine_priority"] != "high",
        r["machine_priority"] == "low",
        r["publication_year"],
        r["title"].casefold(),
    ))

    write_csv(OUTPUT_DIR / "bdtd_records.csv", rows)
    write_json(OUTPUT_DIR / "bdtd_trace.json", trace)
    write_json(OUTPUT_DIR / "bdtd_detail_failures.json", detail_failures)
    summary = {
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "source": "Biblioteca Digital Brasileira de Teses e Dissertações (BDTD/IBICT)",
        "status": status,
        "blocking_error": blocking_error,
        "search_strata_count": len(SEARCH_STRATA),
        "unique_record_links": len(links_to_strata),
        "unique_records_parsed": len(rows),
        "priority_counts": dict(Counter(r["machine_priority"] for r in rows)),
        "document_type_counts": dict(Counter(r["document_type"] or "unknown" for r in rows)),
        "detail_failures": len(detail_failures),
        "language_restrictions": None,
        "date_restrictions": None,
        "document_type_restrictions": None,
        "human_eligibility_decisions_created": 0,
        "prisma_decisions_created": 0,
    }
    write_json(OUTPUT_DIR / "bdtd_summary.json", summary)
    print(json.dumps(summary, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
