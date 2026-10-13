from __future__ import annotations

import csv
import gzip
import hashlib
import json
import os
import re
import time
import unicodedata
import urllib.parse
import urllib.request
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
CANDIDATE_PMIDS = ROOT / "data" / "pubmed_v2_validation" / "pubmed_candidate_union_pmids.csv"
PUBMED_METADATA = Path(os.getenv("PUBMED_UNION_METADATA_PATH", "/tmp/pubmed_artifact/pubmed_union_metadata.csv"))

BVS_URL = "https://search.bvsalud.org/portal/"
SCIELO_URL = "https://search.scielo.org/"
USER_AGENT = "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 Chrome/140.0 Safari/537.36 pfild-review/3.0"
REQUEST_DELAY = float(os.getenv("REGIONAL_REQUEST_DELAY", "0.75"))
PAGE_SIZE = 50
MAX_PAGES = 50

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
    "PF-ILD",
    "PFILD",
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
    "interstitial lung disease", "interstitial lung diseases", "ILD",
    "doença pulmonar intersticial", "doenças pulmonares intersticiais", "DPI",
    "enfermedad pulmonar intersticial", "enfermedades pulmonares intersticiales", "EPI",
]
FIBROSIS_TERMS = ["fibrosing", "fibrotic", "fibrosis", "fibrosante", "fibrose", "fibrótica"]
PROGRESSION_TERMS = ["progressive", "progression", "progressing", "progressiva", "progressivo", "progressão", "progresiva", "progresión"]

PHRASE_QUERY = " OR ".join(f'\"{term}\"' for term in EXACT_PHRASES)
CONCEPT_QUERY = (
    "(" + " OR ".join(f'\"{term}\"' for term in ILD_TERMS) + ") AND "
    "(" + " OR ".join(FIBROSIS_TERMS) + ") AND "
    "(" + " OR ".join(PROGRESSION_TERMS) + ")"
)
ACRONYM_QUERY = (
    '("PF-ILD" OR PFILD OR (PPF AND ("interstitial lung disease" OR "pulmonary fibrosis" OR fibrosing OR fibrotic OR fibrosis)))'
)
SEARCH_STRATA = [
    ("modern_multilingual_phrases", PHRASE_QUERY),
    ("acronym_recall", ACRONYM_QUERY),
    ("conceptual_multilingual_recall", CONCEPT_QUERY),
]

RECORD_FIELDS = [
    "source", "source_record_id", "title", "authors", "journal", "publication_year", "publication_date",
    "doi", "pmid", "abstract", "language", "document_type", "collection", "source_url",
    "search_strata", "exact_phrase_flag", "acronym_flag", "conceptual_recall_flag", "machine_priority",
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
    wanted = {name.casefold() for name in names}
    values: list[str] = []
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
    acronym = bool(re.search(r"\b(?:pf[- ]?ild|pfild|ppf)\b", text, re.I))
    conceptual = (
        any(strip_accents(term.casefold()) in text for term in ILD_TERMS)
        and any(strip_accents(term.casefold()) in text for term in FIBROSIS_TERMS)
        and any(strip_accents(term.casefold()) in text for term in PROGRESSION_TERMS)
    )
    record["exact_phrase_flag"] = exact
    record["acronym_flag"] = acronym
    record["conceptual_recall_flag"] = conceptual
    record["machine_priority"] = "high" if exact else "medium" if acronym or conceptual else "low"
    return record


def request_search(session: requests.Session, url: str, params: dict[str, Any]) -> requests.Response:
    response = session.get(url, params=params, timeout=90, allow_redirects=True)
    response.raise_for_status()
    return response


def extract_resource_links(html: bytes, base_url: str, source: str) -> list[str]:
    soup = BeautifulSoup(html, "lxml")
    links: list[str] = []
    seen: set[str] = set()
    for anchor in soup.find_all("a", href=True):
        href = urljoin(base_url, str(anchor.get("href"))).split("#", 1)[0]
        parsed = urlparse(href)
        host = parsed.netloc.casefold()
        path = parsed.path.casefold()
        query = parsed.query.casefold()
        if source == "LILACS/BVS":
            valid = "bvsalud.org" in host and "/resource/" in path
        else:
            valid = "scielo" in host and host != "search.scielo.org" and (
                "sci_arttext" in query or "pid=" in query or "/article/" in path or "/a/" in path
            )
        if valid and href not in seen:
            seen.add(href)
            links.append(href)
    return links


def parse_detail(html: bytes, url: str, source: str, strata: set[str]) -> dict[str, Any] | None:
    soup = BeautifulSoup(html, "lxml")
    title = first_meta(soup, ["citation_title", "dc.title", "og:title"])
    if not title:
        node = soup.find("h1") or soup.find("h2") or soup.find("title")
        title = normalize_space(node.get_text(" ", strip=True)) if node else ""
    if not title:
        return None
    authors = meta_values(soup, ["citation_author", "dc.creator"])
    journal = first_meta(soup, ["citation_journal_title", "dc.source"])
    pub_date = first_meta(soup, ["citation_publication_date", "citation_date", "dc.date"])
    doi = normalize_doi(first_meta(soup, ["citation_doi", "prism.doi"]))
    if not doi:
        match = re.search(r"\b10\.\d{4,9}/[-._;()/:A-Z0-9]+", soup.get_text(" ", strip=True), re.I)
        doi = normalize_doi(match.group(0)) if match else ""
    pmid = first_meta(soup, ["citation_pmid"])
    abstract = first_meta(soup, ["description", "dc.description", "og:description"])
    language = first_meta(soup, ["citation_language", "dc.language"])
    doc_type = first_meta(soup, ["citation_article_type", "dc.type"])
    path = urlparse(url).path.rstrip("/")
    if source == "LILACS/BVS" and "/resource/" in path:
        source_id = path.split("/")[-1] or stable_id(url)
        collection = "LILACS"
    else:
        # Use the complete URL, including legacy ?pid=, as the source identity.
        source_id = stable_id(url)
        collection = urlparse(url).netloc
    raw_text = soup.get_text(" ", strip=True)
    return apply_flags({
        "source": source,
        "source_record_id": source_id,
        "title": title,
        "authors": "; ".join(authors),
        "journal": journal,
        "publication_year": derive_year(pub_date, raw_text[:2500]),
        "publication_date": pub_date,
        "doi": doi,
        "pmid": pmid,
        "abstract": abstract,
        "language": language,
        "document_type": doc_type,
        "collection": collection,
        "source_url": url,
        "search_strata": "; ".join(sorted(strata)),
        "raw_fields_json": json.dumps({"detail_url": url}, ensure_ascii=False),
    })


def collect_source(session: requests.Session, source: str) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    base_url = BVS_URL if source == "LILACS/BVS" else SCIELO_URL
    trace: list[dict[str, Any]] = []
    detail_trace: list[dict[str, Any]] = []
    link_strata: defaultdict[str, set[str]] = defaultdict(set)
    source_status = "completed"
    blocking_error = ""

    for stratum, query in SEARCH_STRATA:
        seen_this_stratum: set[str] = set()
        previous_signature: tuple[str, ...] | None = None
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
                response = request_search(session, base_url, params)
                raw_meta = save_raw("bvs_search" if source == "LILACS/BVS" else "scielo_search", len(trace) + 1, response)
                links = extract_resource_links(response.content, response.url, source)
                signature = tuple(sorted(links))
                new_this_stratum = [link for link in links if link not in seen_this_stratum]
                for link in links:
                    seen_this_stratum.add(link)
                    link_strata[link].add(stratum)
                trace.append({
                    "source": source, "stratum": stratum, "page": page, "offset": offset,
                    "links": len(links), "new_links_this_stratum": len(new_this_stratum), **raw_meta,
                })
                if not links:
                    break
                if previous_signature is not None and signature == previous_signature:
                    source_status = "pagination_repeat_detected"
                    blocking_error = f"Repeated page detected for {stratum} at page {page}"
                    break
                previous_signature = signature
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
    parsed_source_ids: set[tuple[str, str]] = set()
    if link_strata:
        for idx, (link, strata) in enumerate(sorted(link_strata.items()), start=1):
            try:
                response = session.get(link, timeout=90, allow_redirects=True)
                response.raise_for_status()
                raw_meta = save_raw("bvs_detail" if source == "LILACS/BVS" else "scielo_detail", idx, response)
                record = parse_detail(response.content, response.url, source, strata)
                detail_trace.append({"index": idx, "url": link, "parsed": bool(record), **raw_meta})
                if record:
                    # Only collapse the exact same source representation rediscovered by multiple strata.
                    source_key = (record["source_record_id"], record["source_url"])
                    if source_key not in parsed_source_ids:
                        records.append(record)
                        parsed_source_ids.add(source_key)
                time.sleep(REQUEST_DELAY)
            except Exception as exc:
                detail_trace.append({"index": idx, "url": link, "parsed": False, "error": repr(exc)})

    detail_failures = sum(not bool(item.get("parsed")) for item in detail_trace)
    if source_status == "completed" and detail_failures:
        source_status = "partial_detail_failures"
        blocking_error = f"{detail_failures} detail pages failed or could not be parsed"

    return records, {
        "status": source_status,
        "blocking_error": blocking_error,
        "manual_export_required": source_status != "completed",
        "search_trace": trace,
        "detail_trace": detail_trace,
        "discovered_detail_links": len(link_strata),
        "parsed_records": len(records),
        "detail_failures": detail_failures,
    }


def fetch_pubmed_index_from_ncbi() -> list[dict[str, str]]:
    with CANDIDATE_PMIDS.open(encoding="utf-8-sig", newline="") as handle:
        pmids = [row["pmid"].strip() for row in csv.DictReader(handle) if row.get("pmid", "").strip()]
    if len(pmids) != 2767 or len(set(pmids)) != 2767:
        raise RuntimeError(f"Expected 2767 unique PMIDs, got {len(pmids)} / {len(set(pmids))}")
    rows: list[dict[str, str]] = []
    endpoint = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esummary.fcgi"
    for start in range(0, len(pmids), 100):
        batch = pmids[start:start + 100]
        payload = urllib.parse.urlencode({
            "db": "pubmed", "id": ",".join(batch), "retmode": "json", "tool": "pfild_regional_dedup_index"
        }).encode("utf-8")
        request = urllib.request.Request(endpoint, data=payload, headers={"User-Agent": USER_AGENT}, method="POST")
        last_exc: Exception | None = None
        for attempt in range(1, 6):
            try:
                with urllib.request.urlopen(request, timeout=120) as response:
                    result = json.loads(response.read().decode("utf-8"))["result"]
                for pmid in batch:
                    item = result.get(pmid, {})
                    doi = ""
                    for article_id in item.get("articleids", []) or []:
                        if str(article_id.get("idtype", "")).casefold() == "doi":
                            doi = normalize_doi(str(article_id.get("value", "")))
                            break
                    rows.append({"pmid": pmid, "doi": doi, "normalized_title": normalize_title(str(item.get("title", "")))})
                last_exc = None
                break
            except Exception as exc:
                last_exc = exc
                time.sleep(min(20, 2 ** (attempt - 1)))
        if last_exc is not None:
            raise last_exc
        time.sleep(0.38)
    if len(rows) != 2767:
        raise RuntimeError(f"PubMed dedup index incomplete: {len(rows)} rows")
    return rows


def load_pubmed_index() -> tuple[dict[str, set[str]], dict[str, set[str]], str]:
    rows: list[dict[str, str]] = []
    source = ""
    if PUBMED_METADATA.exists() and PUBMED_METADATA.stat().st_size > 0:
        with PUBMED_METADATA.open(encoding="utf-8-sig", newline="") as handle:
            for row in csv.DictReader(handle):
                rows.append({
                    "pmid": row.get("pmid", "").strip(),
                    "doi": normalize_doi(row.get("doi", "")),
                    "normalized_title": normalize_title(row.get("title", "")),
                })
        source = "frozen_pubmed_union_metadata"
    else:
        rows = fetch_pubmed_index_from_ncbi()
        source = "NCBI_ESummary_regenerated"
    write_csv(OUTPUT_DIR / "pubmed_dedup_index.csv", rows, ["pmid", "doi", "normalized_title"])
    doi_map: defaultdict[str, set[str]] = defaultdict(set)
    title_map: defaultdict[str, set[str]] = defaultdict(set)
    for row in rows:
        if row["doi"] and row["pmid"]:
            doi_map[row["doi"]].add(row["pmid"])
        if row["normalized_title"] and row["pmid"]:
            title_map[row["normalized_title"]].add(row["pmid"])
    return dict(doi_map), dict(title_map), source


def match_pubmed(records: list[dict[str, Any]], doi_map: dict[str, set[str]], title_map: dict[str, set[str]]) -> None:
    for record in records:
        doi = normalize_doi(record.get("doi", ""))
        title = normalize_title(record.get("title", ""))
        doi_pmids = doi_map.get(doi, set()) if doi else set()
        title_pmids = title_map.get(title, set()) if title else set()
        pmids = set(doi_pmids) | set(title_pmids)
        if doi_pmids and title_pmids:
            match_type = "exact_doi_and_title"
        elif doi_pmids:
            match_type = "exact_doi"
        elif title_pmids:
            match_type = "exact_normalized_title"
        else:
            match_type = "none"
        record["pubmed_match_type"] = match_type
        record["pubmed_matching_pmids"] = "; ".join(sorted(pmids))


def build_cross_source_clusters(lilacs: list[dict[str, Any]], scielo: list[dict[str, Any]]) -> list[dict[str, Any]]:
    all_records = lilacs + scielo
    groups: defaultdict[tuple[str, str], list[dict[str, Any]]] = defaultdict(list)
    for record in all_records:
        doi = normalize_doi(record.get("doi", ""))
        title = normalize_title(record.get("title", ""))
        if doi:
            groups[("exact_doi", doi)].append(record)
        if title:
            groups[("exact_normalized_title", title)].append(record)
    out: list[dict[str, Any]] = []
    for (basis, key), members in groups.items():
        sources = {m["source"] for m in members}
        if len(sources) < 2:
            continue
        distinct_titles = {normalize_title(m.get("title", "")) for m in members}
        classification = "cross_source_same_report_candidate"
        if basis == "exact_doi" and len(distinct_titles) > 1:
            classification = "cross_source_doi_collision_review"
        cluster_id = stable_id(basis, key)
        for member in members:
            out.append({
                "cluster_id": cluster_id,
                "match_basis": basis,
                "match_key": key,
                "classification": classification,
                "source": member["source"],
                "source_record_id": member["source_record_id"],
                "title": member["title"],
                "doi": member["doi"],
                "publication_year": member["publication_year"],
                "source_url": member["source_url"],
                "recommended_action": "human review; never merge by DOI alone",
                "human_status": "not reviewed",
            })
    return out


def write_manual_export_protocol(lilacs_trace: dict[str, Any], scielo_trace: dict[str, Any]) -> None:
    blocked = []
    if lilacs_trace["manual_export_required"]:
        blocked.append(f"- LILACS/BVS: {lilacs_trace['status']} — {lilacs_trace['blocking_error']}")
    if scielo_trace["manual_export_required"]:
        blocked.append(f"- SciELO: {scielo_trace['status']} — {scielo_trace['blocking_error']}")
    if not blocked:
        return
    text = f"""# Regional assisted-export protocol\n\nGenerated: {datetime.now(timezone.utc).isoformat()}\n\nAutomated runner collection is incomplete for the following source(s):\n\n{chr(10).join(blocked)}\n\n## Required assisted export\n\nRun all three frozen search strata in the official browser interface for each blocked source.\n\n### LILACS/BVS\n\nInterface: {BVS_URL}\nDatabase filter: LILACS only (`filter[db][]=LILACS`).\nExport every retrieved record in RIS or CSV, without language, date or publication-type limits.\n\n### SciELO\n\nInterface: {SCIELO_URL}\nUse the `subject:` field for each frozen query. Export every retrieved record in RIS or CSV, without restrictions.\n\n### Frozen strata\n\n"""
    for name, query in SEARCH_STRATA:
        text += f"\n#### {name}\n\n```text\n{query}\n```\n"
    text += "\nDo not screen or deduplicate during export. Preserve source-native files and record the local date/time, interface, query, result count and export format.\n"
    (OUTPUT_DIR / "REGIONAL_ASSISTED_EXPORT_REQUIRED.md").write_text(text, encoding="utf-8")


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
    doi_map, title_map, pubmed_index_source = load_pubmed_index()
    match_pubmed(lilacs, doi_map, title_map)
    match_pubmed(scielo, doi_map, title_map)
    clusters = build_cross_source_clusters(lilacs, scielo)

    write_csv(OUTPUT_DIR / "lilacs_records.csv", lilacs, RECORD_FIELDS)
    write_jsonl(OUTPUT_DIR / "lilacs_records.jsonl", lilacs)
    write_csv(OUTPUT_DIR / "scielo_records.csv", scielo, RECORD_FIELDS)
    write_jsonl(OUTPUT_DIR / "scielo_records.jsonl", scielo)
    write_csv(OUTPUT_DIR / "regional_candidate_union.csv", lilacs + scielo, RECORD_FIELDS)
    write_jsonl(OUTPUT_DIR / "regional_candidate_union.jsonl", lilacs + scielo)
    cluster_fields = ["cluster_id", "match_basis", "match_key", "classification", "source", "source_record_id", "title", "doi", "publication_year", "source_url", "recommended_action", "human_status"]
    write_csv(OUTPUT_DIR / "regional_cross_source_clusters.csv", clusters, cluster_fields)
    write_json(OUTPUT_DIR / "lilacs_trace.json", lilacs_trace)
    write_json(OUTPUT_DIR / "scielo_trace.json", scielo_trace)
    write_manual_export_protocol(lilacs_trace, scielo_trace)

    summary = {
        "generated_at_utc": generated,
        "pubmed_dedup_index_source": pubmed_index_source,
        "pubmed_dedup_index_pmids": len({pmid for values in doi_map.values() for pmid in values} | {pmid for values in title_map.values() for pmid in values}),
        "lilacs": {
            "status": lilacs_trace["status"],
            "manual_export_required": lilacs_trace["manual_export_required"],
            "unique_records": len(lilacs),
            "matched_pubmed": sum(r["pubmed_match_type"] != "none" for r in lilacs),
            "not_matched_pubmed": sum(r["pubmed_match_type"] == "none" for r in lilacs),
            "priority_counts": dict(Counter(r["machine_priority"] for r in lilacs)),
            "detail_failures": lilacs_trace["detail_failures"],
        },
        "scielo": {
            "status": scielo_trace["status"],
            "manual_export_required": scielo_trace["manual_export_required"],
            "unique_records": len(scielo),
            "matched_pubmed": sum(r["pubmed_match_type"] != "none" for r in scielo),
            "not_matched_pubmed": sum(r["pubmed_match_type"] == "none" for r in scielo),
            "priority_counts": dict(Counter(r["machine_priority"] for r in scielo)),
            "detail_failures": scielo_trace["detail_failures"],
        },
        "regional_union_records": len(lilacs) + len(scielo),
        "cross_source_cluster_rows": len(clusters),
        "cross_source_cluster_count": len({row["cluster_id"] for row in clusters}),
        "regional_automation_complete": not (lilacs_trace["manual_export_required"] or scielo_trace["manual_export_required"]),
        "human_eligibility_decisions_created": 0,
        "prisma_decisions_created": 0,
    }
    write_json(OUTPUT_DIR / "regional_open_sources_summary.json", summary)
    print(json.dumps(summary, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
