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
OUTPUT_DIR = Path(os.getenv("PFILD_REGIONAL_OUTPUT_DIR", ROOT / "artifacts" / "regional_open_sources"))
RAW_DIR = OUTPUT_DIR / "raw"
PUBMED_METADATA = Path(os.getenv("PUBMED_UNION_METADATA_PATH", "/tmp/pubmed_artifact/pubmed_union_metadata.csv"))

BVS_URL = "https://search.bvsalud.org/portal/"
SCIELO_URL = "https://search.scielo.org/"
USER_AGENT = "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 Chrome/140.0 Safari/537.36 pfild-review/2.0"
REQUEST_DELAY = float(os.getenv("REGIONAL_REQUEST_DELAY", "0.75"))
MAX_PAGES = 40
PAGE_SIZE = 50

EXACT_PHRASES = [
    "progressive pulmonary fibrosis",
    "progressive fibrosing interstitial lung disease",
    "progressive fibrosing interstitial lung diseases",
    "progressive-fibrosing interstitial lung disease",
    "progressive-fibrosing interstitial lung diseases",
    "progressive fibrotic interstitial lung disease",
    "progressive fibrotic interstitial lung diseases",
    "fibrosing interstitial lung disease with a progressive phenotype",
    "fibrosing interstitial lung diseases with a progressive phenotype",
    "progressive fibrosing ild",
    "progressive fibrotic ild",
    "fibrose pulmonar progressiva",
    "doença pulmonar intersticial fibrosante progressiva",
    "doenças pulmonares intersticiais fibrosantes progressivas",
    "doença intersticial pulmonar fibrosante progressiva",
    "fenótipo fibrosante progressivo",
    "fibrosis pulmonar progresiva",
    "enfermedad pulmonar intersticial fibrosante progresiva",
    "enfermedades pulmonares intersticiales fibrosantes progresivas",
    "fenotipo fibrosante progresivo",
]

ILD_TERMS = [
    "interstitial lung disease", "interstitial lung diseases",
    "doença pulmonar intersticial", "doenças pulmonares intersticiais",
    "enfermedad pulmonar intersticial", "enfermedades pulmonares intersticiales",
]
FIBROSIS_TERMS = ["fibrosing", "fibrotic", "fibrosis", "fibrosante", "fibrose", "fibrótica"]
PROGRESSION_TERMS = ["progressive", "progression", "progressing", "progressiva", "progressivo", "progressão", "progresiva", "progresión"]

PHRASE_QUERY = " OR ".join(f'\"{term}\"' for term in EXACT_PHRASES)
CONCEPT_QUERY = (
    "(" + " OR ".join(f'\"{term}\"' for term in ILD_TERMS) + ") AND "
    "(" + " OR ".join(FIBROSIS_TERMS) + ") AND "
    "(" + " OR ".join(PROGRESSION_TERMS) + ")"
)
SEARCH_STRATA = [
    ("modern_multilingual_phrases", PHRASE_QUERY),
    ("conceptual_multilingual_recall", CONCEPT_QUERY),
]

RECORD_FIELDS = [
    "source", "source_record_id", "title", "authors", "journal", "publication_year", "publication_date",
    "doi", "pmid", "abstract", "language", "document_type", "collection", "source_url",
    "search_strata", "exact_phrase_flag", "conceptual_recall_flag", "machine_priority",
    "pubmed_match_type", "pubmed_matching_pmids", "raw_fields_json",
]


def normalize_space(value: str) -> str:
    return re.sub(r"\s+", " ", value or "").strip()


def strip_accents(value: str) -> str:
    return "".join(ch for ch in unicodedata.normalize("NFKD", value) if not unicodedata.combining(ch))


def normalize_title(value: str) -> str:
    return normalize_space(re.sub(r"[^a-z0-9]+", " ", strip_accents(normalize_space(value).casefold())))


def normalize_doi(value: str) -> str:
    value = normalize_space(value).casefold()
    value = re.sub(r"^https?://(?:dx\.)?doi\.org/", "", value)
    value = re.sub(r"^doi:\s*", "", value)
    return value.rstrip(" .;,)")


def derive_year(*values: str) -> str:
    for value in values:
        match = re.search(r"\b(?:18|19|20)\d{2}\b", value or "")
        if match:
            return match.group(0)
    return ""


def stable_id(*parts: str) -> str:
    return hashlib.sha256("\n".join(parts).encode("utf-8")).hexdigest()[:20]


def sha256_bytes(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def write_json(path: Path, obj: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(obj, ensure_ascii=False, indent=2), encoding="utf-8")


def write_csv(path: Path, rows: list[dict[str, Any]], fields: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(row, ensure_ascii=False) + "\n")


def request_once(session: requests.Session, url: str, params: dict[str, Any]) -> requests.Response:
    response = session.get(url, params=params, timeout=90, allow_redirects=True)
    response.raise_for_status()
    return response


def save_raw(prefix: str, index: int, response: requests.Response) -> dict[str, Any]:
    RAW_DIR.mkdir(parents=True, exist_ok=True)
    ctype = response.headers.get("Content-Type", "").lower()
    suffix = "html" if "html" in ctype else "txt"
    path = RAW_DIR / f"{prefix}_{index:03d}.{suffix}.gz"
    with gzip.open(path, "wb") as handle:
        handle.write(response.content)
    return {
        "raw_file": path.name,
        "raw_sha256": sha256_bytes(response.content),
        "content_type": response.headers.get("Content-Type", ""),
        "content_length": len(response.content),
        "final_url": response.url,
        "http_status": response.status_code,
    }


def meta_values(soup: BeautifulSoup, names: list[str]) -> list[str]:
    values: list[str] = []
    wanted = {name.casefold() for name in names}
    for tag in soup.find_all("meta"):
        key = str(tag.get("name") or tag.get("property") or "").casefold()
        if key in wanted:
            value = normalize_space(str(tag.get("content") or ""))
            if value and value not in values:
                values.append(value)
    return values


def first_meta(soup: BeautifulSoup, names: list[str]) -> str:
    values = meta_values(soup, names)
    return values[0] if values else ""


def apply_flags(record: dict[str, Any]) -> dict[str, Any]:
    text = strip_accents(f"{record.get('title', '')}\n{record.get('abstract', '')}".casefold())
    exact = any(strip_accents(term.casefold()) in text for term in EXACT_PHRASES)
    conceptual = (
        any(strip_accents(term.casefold()) in text for term in ILD_TERMS)
        and any(strip_accents(term.casefold()) in text for term in FIBROSIS_TERMS)
        and any(strip_accents(term.casefold()) in text for term in PROGRESSION_TERMS)
    )
    record["exact_phrase_flag"] = exact
    record["conceptual_recall_flag"] = conceptual
    record["machine_priority"] = "high" if exact else "medium" if conceptual else "low"
    return record


def extract_resource_links(html: bytes, base_url: str, source: str) -> list[str]:
    soup = BeautifulSoup(html, "lxml")
    links: list[str] = []
    seen: set[str] = set()
    for anchor in soup.find_all("a", href=True):
        href = urljoin(base_url, str(anchor.get("href")))
        parsed = urlparse(href)
        host = parsed.netloc.casefold()
        path = parsed.path.casefold()
        query = parsed.query.casefold()
        if source == "LILACS/BVS":
            ok = "bvsalud.org" in host and "/resource/" in path
        else:
            ok = "scielo" in host and host != "search.scielo.org" and (
                "sci_arttext" in query or "pid=" in query or "/article/" in path or "/a/" in path
            )
        if not ok:
            continue
        clean = href.split("#", 1)[0]
        if clean not in seen:
            seen.add(clean)
            links.append(clean)
    return links


def parse_detail(html: bytes, url: str, source: str, stratum: str) -> dict[str, Any] | None:
    soup = BeautifulSoup(html, "lxml")
    title = first_meta(soup, ["citation_title", "dc.title", "DC.Title", "og:title"])
    if not title:
        node = soup.find("h1") or soup.find("h2") or soup.find("title")
        title = normalize_space(node.get_text(" ", strip=True)) if node else ""
    if not title:
        return None
    authors = meta_values(soup, ["citation_author", "dc.creator", "DC.Creator"])
    journal = first_meta(soup, ["citation_journal_title", "dc.source", "DC.Source"])
    pub_date = first_meta(soup, ["citation_publication_date", "citation_date", "dc.date", "DC.Date"])
    doi = normalize_doi(first_meta(soup, ["citation_doi", "prism.doi"]))
    if not doi:
        match = re.search(r"\b10\.\d{4,9}/[-._;()/:A-Z0-9]+", soup.get_text(" ", strip=True), re.I)
        doi = normalize_doi(match.group(0)) if match else ""
    pmid = first_meta(soup, ["citation_pmid"])
    abstract = first_meta(soup, ["description", "dc.description", "DC.Description", "og:description"])
    language = first_meta(soup, ["citation_language", "dc.language", "DC.Language"])
    doc_type = first_meta(soup, ["citation_article_type", "dc.type", "DC.Type"])
    path = urlparse(url).path.rstrip("/")
    source_id = path.split("/")[-1] if source == "LILACS/BVS" and "/resource/" in path else (doi or stable_id(url, title))
    collection = "LILACS" if source == "LILACS/BVS" else urlparse(url).netloc
    raw_text = soup.get_text(" ", strip=True)
    return apply_flags({
        "source": source,
        "source_record_id": source_id,
        "title": title,
        "authors": "; ".join(authors),
        "journal": journal,
        "publication_year": derive_year(pub_date, raw_text[:2000]),
        "publication_date": pub_date,
        "doi": doi,
        "pmid": pmid,
        "abstract": abstract,
        "language": language,
        "document_type": doc_type,
        "collection": collection,
        "source_url": url,
        "search_strata": stratum,
        "raw_fields_json": json.dumps({"detail_url": url}, ensure_ascii=False),
    })


def collect_source(session: requests.Session, source: str) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    base_url = BVS_URL if source == "LILACS/BVS" else SCIELO_URL
    trace: list[dict[str, Any]] = []
    detail_trace: list[dict[str, Any]] = []
    source_status = "completed"
    blocking_error = ""
    link_strata: defaultdict[str, set[str]] = defaultdict(set)

    for stratum, query in SEARCH_STRATA:
        for page in range(1, MAX_PAGES + 1):
            offset = (page - 1) * PAGE_SIZE
            if source == "LILACS/BVS":
                params: dict[str, Any] = {
                    "lang": "en", "q": query, "count": PAGE_SIZE, "page": page, "from": offset,
                    "output": "site", "format": "summary", "filter[db][]": "LILACS",
                }
            else:
                params = {"lang": "en", "q": f"subject:({query})", "count": PAGE_SIZE, "page": page, "from": offset}
            try:
                response = request_once(session, base_url, params)
                raw_meta = save_raw("bvs_search" if source == "LILACS/BVS" else "scielo_search", len(trace) + 1, response)
                links = extract_resource_links(response.content, response.url, source)
                new_links = 0
                for link in links:
                    if not link_strata[link]:
                        new_links += 1
                    link_strata[link].add(stratum)
                trace.append({"source": source, "stratum": stratum, "page": page, "offset": offset,
                              "links": len(links), "new_links": new_links, **raw_meta})
                if not links or new_links == 0:
                    break
                time.sleep(REQUEST_DELAY)
            except requests.HTTPError as exc:
                status = exc.response.status_code if exc.response is not None else None
                source_status = f"blocked_http_{status}" if status else "request_failed"
                blocking_error = repr(exc)
                trace.append({"source": source, "stratum": stratum, "page": page, "offset": offset,
                              "error": blocking_error, "http_status": status})
                break
            except Exception as exc:
                source_status = "request_failed"
                blocking_error = repr(exc)
                trace.append({"source": source, "stratum": stratum, "page": page, "offset": offset, "error": blocking_error})
                break
        if source_status != "completed":
            break

    records: list[dict[str, Any]] = []
    if source_status == "completed":
        for idx, (link, strata) in enumerate(sorted(link_strata.items()), start=1):
            try:
                response = request_once(session, link, {})
                raw_meta = save_raw("bvs_detail" if source == "LILACS/BVS" else "scielo_detail", idx, response)
                record = parse_detail(response.content, response.url, source, "; ".join(sorted(strata)))
                detail_trace.append({"index": idx, "url": link, "parsed": bool(record), **raw_meta})
                if record:
                    records.append(record)
                time.sleep(REQUEST_DELAY)
            except Exception as exc:
                detail_trace.append({"index": idx, "url": link, "parsed": False, "error": repr(exc)})

    unique: dict[str, dict[str, Any]] = {}
    provenance: defaultdict[str, set[str]] = defaultdict(set)
    for record in records:
        key = normalize_doi(record.get("doi", "")) or record.get("source_record_id", "") or normalize_title(record.get("title", ""))
        if key not in unique:
            unique[key] = record
        provenance[key].update(item for item in record.get("search_strata", "").split("; ") if item)
    for key, record in unique.items():
        record["search_strata"] = "; ".join(sorted(provenance[key]))

    return list(unique.values()), {
        "status": source_status,
        "blocking_error": blocking_error,
        "manual_export_required": source_status != "completed",
        "search_trace": trace,
        "detail_trace": detail_trace,
        "discovered_detail_links": len(link_strata),
    }


def load_pubmed_index() -> tuple[dict[str, set[str]], dict[str, set[str]]]:
    doi_map: defaultdict[str, set[str]] = defaultdict(set)
    title_map: defaultdict[str, set[str]] = defaultdict(set)
    with PUBMED_METADATA.open(encoding="utf-8-sig", newline="") as handle:
        for row in csv.DictReader(handle):
            pmid = row.get("pmid", "").strip()
            doi = normalize_doi(row.get("doi", ""))
            title = normalize_title(row.get("title", ""))
            if doi and pmid:
                doi_map[doi].add(pmid)
            if title and pmid:
                title_map[title].add(pmid)
    return dict(doi_map), dict(title_map)


def match_pubmed(records: list[dict[str, Any]], doi_map: dict[str, set[str]], title_map: dict[str, set[str]]) -> None:
    for record in records:
        pmids: set[str] = set()
        match_type = "none"
        doi = normalize_doi(record.get("doi", ""))
        title = normalize_title(record.get("title", ""))
        if doi and doi in doi_map:
            pmids.update(doi_map[doi]); match_type = "exact_doi"
        if not pmids and title and title in title_map:
            pmids.update(title_map[title]); match_type = "exact_normalized_title"
        record["pubmed_match_type"] = match_type
        record["pubmed_matching_pmids"] = "; ".join(sorted(pmids))


def main() -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    RAW_DIR.mkdir(parents=True, exist_ok=True)
    session = requests.Session()
    session.headers.update({
        "User-Agent": USER_AGENT,
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.9,pt-BR;q=0.8,es;q=0.7",
        "Cache-Control": "no-cache",
    })

    generated = datetime.now(timezone.utc).isoformat()
    write_json(OUTPUT_DIR / "regional_search_queries.json", {
        "generated_at_utc": generated,
        "bvs_interface": BVS_URL,
        "bvs_database_filter": "filter[db][]=LILACS",
        "scielo_interface": SCIELO_URL,
        "strata": [{"name": name, "query": query} for name, query in SEARCH_STRATA],
        "language_restrictions": None,
        "date_restrictions": None,
        "publication_type_restrictions": None,
        "human_eligibility_decisions_created": 0,
        "prisma_decisions_created": 0,
    })

    lilacs, lilacs_trace = collect_source(session, "LILACS/BVS")
    scielo, scielo_trace = collect_source(session, "SciELO")
    doi_map, title_map = load_pubmed_index()
    match_pubmed(lilacs, doi_map, title_map)
    match_pubmed(scielo, doi_map, title_map)

    write_csv(OUTPUT_DIR / "lilacs_records.csv", lilacs, RECORD_FIELDS)
    write_jsonl(OUTPUT_DIR / "lilacs_records.jsonl", lilacs)
    write_csv(OUTPUT_DIR / "scielo_records.csv", scielo, RECORD_FIELDS)
    write_jsonl(OUTPUT_DIR / "scielo_records.jsonl", scielo)
    write_json(OUTPUT_DIR / "lilacs_trace.json", lilacs_trace)
    write_json(OUTPUT_DIR / "scielo_trace.json", scielo_trace)

    union = lilacs + scielo
    write_csv(OUTPUT_DIR / "regional_candidate_union.csv", union, RECORD_FIELDS)
    write_jsonl(OUTPUT_DIR / "regional_candidate_union.jsonl", union)

    summary = {
        "generated_at_utc": generated,
        "lilacs": {
            "status": lilacs_trace["status"],
            "manual_export_required": lilacs_trace["manual_export_required"],
            "unique_records": len(lilacs),
            "matched_pubmed": sum(r.get("pubmed_match_type") != "none" for r in lilacs),
            "not_matched_pubmed": sum(r.get("pubmed_match_type") == "none" for r in lilacs),
            "priority_counts": dict(Counter(r["machine_priority"] for r in lilacs)),
        },
        "scielo": {
            "status": scielo_trace["status"],
            "manual_export_required": scielo_trace["manual_export_required"],
            "unique_records": len(scielo),
            "matched_pubmed": sum(r.get("pubmed_match_type") != "none" for r in scielo),
            "not_matched_pubmed": sum(r.get("pubmed_match_type") == "none" for r in scielo),
            "priority_counts": dict(Counter(r["machine_priority"] for r in scielo)),
        },
        "regional_union_records": len(union),
        "regional_automation_complete": not (lilacs_trace["manual_export_required"] or scielo_trace["manual_export_required"]),
        "human_eligibility_decisions_created": 0,
        "prisma_decisions_created": 0,
    }
    write_json(OUTPUT_DIR / "regional_open_sources_summary.json", summary)
    print(json.dumps(summary, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
