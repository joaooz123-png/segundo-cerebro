from __future__ import annotations

import csv
import gzip
import hashlib
import json
import os
import re
import time
import unicodedata
import xml.etree.ElementTree as ET
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from urllib.parse import urljoin, urlparse

import requests
from bs4 import BeautifulSoup

ROOT = Path(__file__).resolve().parents[1]
OUTPUT_DIR = Path(os.getenv("PFILD_REGIONAL_OUTPUT_DIR", ROOT / "artifacts" / "regional_open_sources"))
PUBMED_METADATA = Path(os.getenv("PUBMED_UNION_METADATA_PATH", "/tmp/pubmed_artifact/pubmed_union_metadata.csv"))
RAW_DIR = OUTPUT_DIR / "raw"

BVS_URL = "https://pesquisa.bvsalud.org/portal/"
SCIELO_URL = "https://search.scielo.org/"
USER_AGENT = "pfild_ppf_systematic_review/1.4 (+https://github.com/joaooz123-png/segundo-cerebro)"
REQUEST_DELAY = float(os.getenv("REGIONAL_REQUEST_DELAY", "0.65"))
MAX_RETRIES = 5
LILACS_PAGE_SIZE = 200
SCIELO_PAGE_SIZE = 50
MAX_LILACS_PAGES = 50
MAX_SCIELO_PAGES = 30

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
    "interstitial lung disease", "interstitial lung diseases", "ild",
    "doença pulmonar intersticial", "doenças pulmonares intersticiais", "dpi",
    "enfermedad pulmonar intersticial", "enfermedades pulmonares intersticiales", "epi",
]
FIBROSIS_TERMS = [
    "fibrosing", "fibrotic", "fibrosis", "fibrosante", "fibrótica", "fibrotic",
    "fibrose", "fibrosis",
]
PROGRESSION_TERMS = [
    "progressive", "progression", "progressing", "progressiva", "progressivo", "progressão",
    "progresiva", "progresivo", "progresión",
]

PHRASE_QUERY = " OR ".join(f'\"{term}\"' for term in EXACT_PHRASES)
CONCEPT_QUERY = (
    "(" + " OR ".join(f'\"{term}\"' for term in ILD_TERMS if len(term) > 3) + ") AND "
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
    value = strip_accents(normalize_space(value).casefold())
    return normalize_space(re.sub(r"[^a-z0-9]+", " ", value))


def normalize_doi(value: str) -> str:
    value = normalize_space(value).casefold()
    value = re.sub(r"^https?://(?:dx\.)?doi\.org/", "", value)
    value = re.sub(r"^doi:\s*", "", value)
    return value.rstrip(" .;,)")


def sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def stable_id(*parts: str) -> str:
    return hashlib.sha256("\n".join(parts).encode("utf-8")).hexdigest()[:20]


def write_csv(path: Path, rows: list[dict[str, Any]], fields: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2), encoding="utf-8")


def append_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(row, ensure_ascii=False) + "\n")


def request(session: requests.Session, url: str, params: dict[str, Any] | None = None) -> requests.Response:
    for attempt in range(1, MAX_RETRIES + 1):
        try:
            response = session.get(url, params=params, timeout=90)
            if response.status_code == 429 or response.status_code >= 500:
                raise requests.HTTPError(f"HTTP {response.status_code}")
            response.raise_for_status()
            return response
        except (requests.RequestException, TimeoutError) as exc:
            if attempt == MAX_RETRIES:
                raise
            wait = min(30.0, 2 ** (attempt - 1))
            print(f"request failed attempt={attempt} url={url}: {exc}; retry {wait:.1f}s")
            time.sleep(wait)
    raise RuntimeError("unreachable")


def text_value(node: ET.Element) -> str:
    return normalize_space(" ".join(part for part in node.itertext() if part))


def parse_solr_doc(doc: ET.Element) -> dict[str, Any]:
    fields: dict[str, Any] = {}
    for child in list(doc):
        name = child.attrib.get("name", child.tag)
        if child.tag in {"arr", "lst"}:
            values = [text_value(item) for item in list(child) if text_value(item)]
            fields[name] = values
        else:
            fields[name] = text_value(child)
    return fields


def parse_generic_record(node: ET.Element) -> dict[str, Any]:
    fields: dict[str, Any] = {}
    for child in list(node):
        name = child.attrib.get("name", child.tag)
        value = text_value(child)
        if not value:
            continue
        if name in fields:
            current = fields[name]
            fields[name] = current + [value] if isinstance(current, list) else [current, value]
        else:
            fields[name] = value
    return fields


def flatten_value(value: Any) -> str:
    if isinstance(value, list):
        return "; ".join(normalize_space(str(item)) for item in value if normalize_space(str(item)))
    return normalize_space(str(value or ""))


def first_field(fields: dict[str, Any], names: list[str]) -> str:
    lower = {str(key).casefold(): value for key, value in fields.items()}
    for name in names:
        if name.casefold() in lower:
            value = flatten_value(lower[name.casefold()])
            if value:
                return value
    return ""


def find_doi(fields: dict[str, Any], raw_text: str) -> str:
    for key, value in fields.items():
        if "doi" in str(key).casefold():
            found = normalize_doi(flatten_value(value))
            if found.startswith("10."):
                return found
    match = re.search(r"\b10\.\d{4,9}/[-._;()/:A-Z0-9]+", raw_text, re.I)
    return normalize_doi(match.group(0)) if match else ""


def derive_year(*values: str) -> str:
    for value in values:
        match = re.search(r"\b(?:18|19|20)\d{2}\b", value or "")
        if match:
            return match.group(0)
    return ""


def apply_flags(record: dict[str, Any]) -> dict[str, Any]:
    combined = strip_accents(f"{record.get('title', '')}\n{record.get('abstract', '')}".casefold())
    exact = any(strip_accents(term.casefold()) in combined for term in EXACT_PHRASES)
    has_ild = any(strip_accents(term.casefold()) in combined for term in ILD_TERMS if len(term) > 3)
    has_fibrosis = any(strip_accents(term.casefold()) in combined for term in FIBROSIS_TERMS)
    has_progression = any(strip_accents(term.casefold()) in combined for term in PROGRESSION_TERMS)
    conceptual = has_ild and has_fibrosis and has_progression
    record["exact_phrase_flag"] = exact
    record["conceptual_recall_flag"] = conceptual
    record["machine_priority"] = "high" if exact else "medium" if conceptual else "low"
    return record


def parse_lilacs_xml(raw: bytes, stratum: str, query: str) -> tuple[list[dict[str, Any]], int | None]:
    root = ET.fromstring(raw)
    total = None
    for node in root.iter():
        for attr in ("numFound", "total", "count"):
            if attr in node.attrib and str(node.attrib[attr]).isdigit():
                candidate = int(node.attrib[attr])
                if total is None or candidate > total:
                    total = candidate
    docs = root.findall(".//doc")
    parsed_fields = [parse_solr_doc(doc) for doc in docs]
    if not parsed_fields:
        records = root.findall(".//record")
        parsed_fields = [parse_generic_record(record) for record in records]
    if not parsed_fields:
        items = root.findall(".//item")
        parsed_fields = [parse_generic_record(item) for item in items]

    results = []
    for fields in parsed_fields:
        raw_text = json.dumps(fields, ensure_ascii=False)
        title = first_field(fields, ["title", "ti", "title_pt", "title_es", "title_en"])
        authors = first_field(fields, ["author", "authors", "au", "creator"])
        journal = first_field(fields, ["journal", "journal_title", "source", "fo", "ta"])
        pub_date = first_field(fields, ["publication_date", "date", "da", "year_cluster", "year"])
        year = derive_year(pub_date, raw_text)
        doi = find_doi(fields, raw_text)
        pmid = first_field(fields, ["pmid", "pubmed_id"])
        abstract = first_field(fields, ["abstract", "ab", "summary", "description"])
        language = first_field(fields, ["language", "la", "lang"])
        doc_type = first_field(fields, ["publication_type", "type", "pt", "document_type"])
        collection = first_field(fields, ["db", "database", "collection"]) or "LILACS"
        source_url = first_field(fields, ["url", "link", "fulltext", "resource_url"])
        source_id = first_field(fields, ["id", "lilacs_id", "identifier", "db_id"])
        if not source_id:
            source_id = stable_id(title, authors, journal, year, doi)
        if not source_url and source_id:
            source_url = f"https://pesquisa.bvsalud.org/portal/resource/en/{source_id}"
        if not title:
            continue
        results.append(apply_flags({
            "source": "LILACS/BVS",
            "source_record_id": source_id,
            "title": title,
            "authors": authors,
            "journal": journal,
            "publication_year": year,
            "publication_date": pub_date,
            "doi": doi,
            "pmid": pmid,
            "abstract": abstract,
            "language": language,
            "document_type": doc_type,
            "collection": collection,
            "source_url": source_url,
            "search_strata": stratum,
            "raw_fields_json": json.dumps(fields, ensure_ascii=False, sort_keys=True),
        }))
    return results, total


def collect_lilacs(session: requests.Session) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    RAW_DIR.mkdir(parents=True, exist_ok=True)
    all_records: dict[str, dict[str, Any]] = {}
    provenance: defaultdict[str, set[str]] = defaultdict(set)
    trace = []
    for stratum, query in SEARCH_STRATA:
        offset = 0
        page = 0
        reported_total = None
        while page < MAX_LILACS_PAGES:
            page += 1
            params = {
                "q": query,
                "filter": "db:LILACS",
                "output": "xml",
                "count": LILACS_PAGE_SIZE,
                "from": offset,
                "lang": "en",
            }
            response = request(session, BVS_URL, params=params)
            raw = response.content
            raw_path = RAW_DIR / f"lilacs_{stratum}_{page:03d}.xml.gz"
            with gzip.open(raw_path, "wb") as handle:
                handle.write(raw)
            records, total = parse_lilacs_xml(raw, stratum, query)
            if total is not None:
                reported_total = total
            trace.append({
                "stratum": stratum,
                "page": page,
                "offset": offset,
                "records_parsed": len(records),
                "reported_total": reported_total,
                "request_url": response.url,
                "raw_file": raw_path.name,
                "raw_sha256": sha256_bytes(raw),
            })
            if not records:
                break
            for record in records:
                key = record["source_record_id"] or normalize_doi(record["doi"]) or normalize_title(record["title"])
                if key not in all_records:
                    all_records[key] = record
                provenance[key].add(stratum)
            offset += LILACS_PAGE_SIZE
            if reported_total is not None and offset >= reported_total:
                break
            if len(records) < LILACS_PAGE_SIZE:
                break
            time.sleep(REQUEST_DELAY)
    for key, record in all_records.items():
        record["search_strata"] = "; ".join(sorted(provenance[key]))
    return list(all_records.values()), {"trace": trace}


def meta_content(soup: BeautifulSoup, names: list[str], multi: bool = False) -> str | list[str]:
    values = []
    for name in names:
        for tag in soup.find_all("meta", attrs={"name": re.compile(f"^{re.escape(name)}$", re.I)}):
            value = normalize_space(tag.get("content", ""))
            if value:
                values.append(value)
        for tag in soup.find_all("meta", attrs={"property": re.compile(f"^{re.escape(name)}$", re.I)}):
            value = normalize_space(tag.get("content", ""))
            if value:
                values.append(value)
    if multi:
        seen = []
        for value in values:
            if value not in seen:
                seen.append(value)
        return seen
    return values[0] if values else ""


def canonicalize_scielo_url(url: str) -> str:
    parsed = urlparse(url)
    return parsed._replace(query="", fragment="").geturl().rstrip("/")


def extract_scielo_result_links(html: bytes, base_url: str) -> list[str]:
    soup = BeautifulSoup(html, "lxml")
    links = []
    seen = set()
    for anchor in soup.find_all("a", href=True):
        href = urljoin(base_url, anchor.get("href", ""))
        parsed = urlparse(href)
        host = parsed.netloc.casefold()
        path = parsed.path.casefold()
        query = parsed.query.casefold()
        if "scielo" not in host or host == "search.scielo.org":
            continue
        article_like = (
            "sci_arttext" in query or "pid=" in query or "/article/" in path or
            ("/j/" in path and ("/a/" in path or "/abstract/" in path or "/full/" in path))
        )
        if not article_like:
            continue
        clean = canonicalize_scielo_url(href)
        if clean not in seen:
            seen.add(clean)
            links.append(clean)
    return links


def parse_scielo_article(html: bytes, url: str, strata: set[str]) -> dict[str, Any] | None:
    soup = BeautifulSoup(html, "lxml")
    title = meta_content(soup, ["citation_title", "dc.title", "DC.Title", "og:title"])
    if not title:
        title_tag = soup.find("title")
        title = normalize_space(title_tag.get_text(" ", strip=True)) if title_tag else ""
    if not title:
        return None
    authors = meta_content(soup, ["citation_author", "dc.creator", "DC.Creator"], multi=True)
    journal = meta_content(soup, ["citation_journal_title", "dc.source", "DC.Source"])
    pub_date = meta_content(soup, ["citation_publication_date", "citation_date", "dc.date", "DC.Date"])
    doi = normalize_doi(meta_content(soup, ["citation_doi", "dc.identifier", "DC.Identifier"]))
    if not doi:
        match = re.search(r"\b10\.\d{4,9}/[-._;()/:A-Z0-9]+", soup.get_text(" ", strip=True), re.I)
        doi = normalize_doi(match.group(0)) if match else ""
    abstract = meta_content(soup, ["description", "dc.description", "DC.Description", "og:description"])
    language = meta_content(soup, ["citation_language", "dc.language", "DC.Language"])
    doc_type = meta_content(soup, ["citation_article_type", "dc.type", "DC.Type"])
    canonical_tag = soup.find("link", rel=lambda value: value and "canonical" in value)
    canonical = canonical_tag.get("href", "") if canonical_tag else url
    canonical = canonicalize_scielo_url(urljoin(url, canonical))
    collection = urlparse(canonical).netloc
    record = {
        "source": "SciELO",
        "source_record_id": doi or stable_id(canonical, title),
        "title": normalize_space(str(title)),
        "authors": "; ".join(authors) if isinstance(authors, list) else str(authors),
        "journal": normalize_space(str(journal)),
        "publication_year": derive_year(str(pub_date), soup.get_text(" ", strip=True)[:2000]),
        "publication_date": normalize_space(str(pub_date)),
        "doi": doi,
        "pmid": normalize_space(str(meta_content(soup, ["citation_pmid"]))),
        "abstract": normalize_space(str(abstract)),
        "language": normalize_space(str(language)),
        "document_type": normalize_space(str(doc_type)),
        "collection": collection,
        "source_url": canonical,
        "search_strata": "; ".join(sorted(strata)),
        "raw_fields_json": json.dumps({"canonical_url": canonical}, ensure_ascii=False),
    }
    return apply_flags(record)


def collect_scielo(session: requests.Session) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    link_strata: defaultdict[str, set[str]] = defaultdict(set)
    trace = []
    for stratum, query in SEARCH_STRATA:
        stagnant = 0
        for page in range(1, MAX_SCIELO_PAGES + 1):
            start = 1 + (page - 1) * SCIELO_PAGE_SIZE
            params = {
                "q": query,
                "lang": "pt",
                "count": SCIELO_PAGE_SIZE,
                "from": start,
                "output": "site",
                "format": "summary",
                "page": page,
            }
            response = request(session, SCIELO_URL, params=params)
            raw = response.content
            raw_path = RAW_DIR / f"scielo_search_{stratum}_{page:03d}.html.gz"
            with gzip.open(raw_path, "wb") as handle:
                handle.write(raw)
            links = extract_scielo_result_links(raw, response.url)
            new_count = 0
            for link in links:
                if stratum not in link_strata[link]:
                    if not link_strata[link]:
                        new_count += 1
                    link_strata[link].add(stratum)
            trace.append({
                "stratum": stratum,
                "page": page,
                "from": start,
                "article_links_on_page": len(links),
                "new_unique_links": new_count,
                "request_url": response.url,
                "raw_file": raw_path.name,
                "raw_sha256": sha256_bytes(raw),
            })
            if not links or new_count == 0:
                stagnant += 1
            else:
                stagnant = 0
            if stagnant >= 2:
                break
            time.sleep(REQUEST_DELAY)

    records = []
    article_trace = []
    for index, (link, strata) in enumerate(sorted(link_strata.items()), start=1):
        try:
            response = request(session, link)
            raw = response.content
            raw_path = RAW_DIR / f"scielo_article_{index:04d}.html.gz"
            with gzip.open(raw_path, "wb") as handle:
                handle.write(raw)
            record = parse_scielo_article(raw, response.url, strata)
            article_trace.append({
                "index": index,
                "requested_url": link,
                "final_url": response.url,
                "parsed": bool(record),
                "raw_file": raw_path.name,
                "raw_sha256": sha256_bytes(raw),
            })
            if record:
                records.append(record)
        except Exception as exc:
            article_trace.append({"index": index, "requested_url": link, "parsed": False, "error": repr(exc)})
        time.sleep(REQUEST_DELAY)

    unique: dict[str, dict[str, Any]] = {}
    provenance: defaultdict[str, set[str]] = defaultdict(set)
    for record in records:
        key = normalize_doi(record["doi"]) or canonicalize_scielo_url(record["source_url"]) or normalize_title(record["title"])
        if key not in unique:
            unique[key] = record
        provenance[key].update(record["search_strata"].split("; "))
    for key, record in unique.items():
        record["search_strata"] = "; ".join(sorted(item for item in provenance[key] if item))
    return list(unique.values()), {"search_trace": trace, "article_trace": article_trace}


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
        doi = normalize_doi(record.get("doi", ""))
        title = normalize_title(record.get("title", ""))
        pmids: set[str] = set()
        match_type = "none"
        if doi and doi in doi_map:
            pmids.update(doi_map[doi])
            match_type = "exact_doi"
        if not pmids and title and title in title_map:
            pmids.update(title_map[title])
            match_type = "exact_normalized_title"
        record["pubmed_match_type"] = match_type
        record["pubmed_matching_pmids"] = "; ".join(sorted(pmids))


def regional_union(lilacs: list[dict[str, Any]], scielo: list[dict[str, Any]]) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    records = lilacs + scielo
    clusters: defaultdict[str, list[dict[str, Any]]] = defaultdict(list)
    for record in records:
        doi = normalize_doi(record.get("doi", ""))
        title = normalize_title(record.get("title", ""))
        key = f"doi:{doi}" if doi else f"title:{title}" if title else f"id:{record['source']}:{record['source_record_id']}"
        clusters[key].append(record)
    cross = []
    for key, members in clusters.items():
        sources = {member["source"] for member in members}
        if len(members) > 1 and len(sources) > 1:
            for member in members:
                cross.append({
                    "cluster_key": key,
                    "source": member["source"],
                    "source_record_id": member["source_record_id"],
                    "title": member["title"],
                    "doi": member["doi"],
                    "publication_year": member["publication_year"],
                    "source_url": member["source_url"],
                    "recommended_action": "review as possible same-report source representation; do not auto-merge",
                    "human_status": "not reviewed",
                })
    return records, cross


def main() -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    RAW_DIR.mkdir(parents=True, exist_ok=True)
    session = requests.Session()
    session.headers.update({"User-Agent": USER_AGENT, "Accept-Language": "en,pt-BR;q=0.9,es;q=0.8"})

    queries = {
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "lilacs_interface": BVS_URL,
        "scielo_interface": SCIELO_URL,
        "strata": [{"name": name, "query": query} for name, query in SEARCH_STRATA],
        "language_restrictions": None,
        "date_restrictions": None,
        "document_type_restrictions": None,
        "eligibility_decisions_created": 0,
    }
    write_json(OUTPUT_DIR / "regional_search_queries.json", queries)

    lilacs, lilacs_trace = collect_lilacs(session)
    scielo, scielo_trace = collect_scielo(session)
    doi_map, title_map = load_pubmed_index()
    match_pubmed(lilacs, doi_map, title_map)
    match_pubmed(scielo, doi_map, title_map)
    union, cross_clusters = regional_union(lilacs, scielo)

    write_csv(OUTPUT_DIR / "lilacs_records.csv", lilacs, RECORD_FIELDS)
    append_jsonl(OUTPUT_DIR / "lilacs_records.jsonl", lilacs)
    write_csv(OUTPUT_DIR / "scielo_records.csv", scielo, RECORD_FIELDS)
    append_jsonl(OUTPUT_DIR / "scielo_records.jsonl", scielo)
    write_csv(OUTPUT_DIR / "regional_candidate_union.csv", union, RECORD_FIELDS)
    append_jsonl(OUTPUT_DIR / "regional_candidate_union.jsonl", union)
    cluster_fields = [
        "cluster_key", "source", "source_record_id", "title", "doi", "publication_year",
        "source_url", "recommended_action", "human_status",
    ]
    write_csv(OUTPUT_DIR / "regional_cross_source_clusters.csv", cross_clusters, cluster_fields)
    write_json(OUTPUT_DIR / "lilacs_trace.json", lilacs_trace)
    write_json(OUTPUT_DIR / "scielo_trace.json", scielo_trace)

    summary = {
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "lilacs": {
            "unique_records": len(lilacs),
            "matched_pubmed": sum(r["pubmed_match_type"] != "none" for r in lilacs),
            "not_matched_pubmed": sum(r["pubmed_match_type"] == "none" for r in lilacs),
            "priority_counts": dict(Counter(r["machine_priority"] for r in lilacs)),
            "search_pages": len(lilacs_trace["trace"]),
        },
        "scielo": {
            "unique_records": len(scielo),
            "matched_pubmed": sum(r["pubmed_match_type"] != "none" for r in scielo),
            "not_matched_pubmed": sum(r["pubmed_match_type"] == "none" for r in scielo),
            "priority_counts": dict(Counter(r["machine_priority"] for r in scielo)),
            "search_pages": len(scielo_trace["search_trace"]),
            "article_pages_attempted": len(scielo_trace["article_trace"]),
            "article_pages_parsed": sum(bool(item.get("parsed")) for item in scielo_trace["article_trace"]),
        },
        "regional_union_raw_records_before_cross_source_dedup": len(union),
        "cross_source_cluster_rows": len(cross_clusters),
        "cross_source_cluster_count": len({r["cluster_key"] for r in cross_clusters}),
        "human_eligibility_decisions_created": 0,
        "prisma_decisions_created": 0,
    }
    write_json(OUTPUT_DIR / "regional_open_sources_summary.json", summary)
    print(json.dumps(summary, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
