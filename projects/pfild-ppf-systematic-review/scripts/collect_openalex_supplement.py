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
from urllib.parse import urlparse

import requests

ROOT = Path(__file__).resolve().parents[1]
OUTPUT_DIR = Path(os.getenv("PFILD_OPENALEX_OUTPUT_DIR", ROOT / "artifacts" / "openalex_supplement"))
RAW_DIR = OUTPUT_DIR / "raw"
CANDIDATE_PMIDS = ROOT / "data" / "pubmed_v2_validation" / "pubmed_candidate_union_pmids.csv"
EUROPE_PMC = ROOT / "data" / "g2_open_sources" / "europe_pmc_records.csv"

OPENALEX_URL = "https://api.openalex.org/works"
USER_AGENT = "pfild-ppf-systematic-review/1.0 (+https://github.com/joaooz123-png/segundo-cerebro)"
REQUEST_DELAY = float(os.getenv("OPENALEX_REQUEST_DELAY", "0.20"))
MAX_RETRIES = 6
MAX_PAGES_PER_TERM = int(os.getenv("OPENALEX_MAX_PAGES_PER_TERM", "100"))
PER_PAGE = 200

SEARCH_TERMS = [
    "progressive pulmonary fibrosis",
    "progressive fibrosing interstitial lung disease",
    "progressive fibrosing interstitial lung diseases",
    "progressive-fibrosing interstitial lung disease",
    "progressive-fibrosing interstitial lung diseases",
    "progressive fibrotic interstitial lung disease",
    "progressive fibrotic interstitial lung diseases",
    "progressive fibrosing ILD",
    "progressive fibrotic ILD",
    "PF-ILD",
    "PFILD",
    "PPF interstitial lung disease",
    "fibrosing interstitial lung disease progressive phenotype",
    "fibrosing interstitial lung diseases progressive phenotype",
    "fibrose pulmonar progressiva",
    "doença pulmonar intersticial fibrosante progressiva",
    "fenótipo fibrosante progressivo",
    "fibrosis pulmonar progresiva",
    "enfermedad pulmonar intersticial fibrosante progresiva",
    "fenotipo fibrosante progresivo",
]

EXACT_PHRASES = [
    "progressive pulmonary fibrosis",
    "progressive fibrosing interstitial lung disease",
    "progressive fibrosing interstitial lung diseases",
    "progressive-fibrosing interstitial lung disease",
    "progressive-fibrosing interstitial lung diseases",
    "progressive fibrotic interstitial lung disease",
    "progressive fibrotic interstitial lung diseases",
    "progressive fibrosing ild",
    "progressive fibrotic ild",
    "fibrose pulmonar progressiva",
    "doença pulmonar intersticial fibrosante progressiva",
    "fenótipo fibrosante progressivo",
    "fibrosis pulmonar progresiva",
    "enfermedad pulmonar intersticial fibrosante progresiva",
    "fenotipo fibrosante progresivo",
]

GREY_LIKE_TYPES = {
    "dissertation",
    "book-chapter",
    "book",
    "proceedings-article",
    "report",
    "reference-entry",
    "other",
}

FIELDS = [
    "openalex_id",
    "title",
    "publication_year",
    "publication_date",
    "work_type",
    "doi",
    "pmid",
    "authors",
    "source_name",
    "source_type",
    "language",
    "cited_by_count",
    "referenced_works_count",
    "is_retracted",
    "open_access_status",
    "search_terms",
    "explicit_phrase_flag",
    "acronym_context_flag",
    "grey_like_type_flag",
    "pubmed_match",
    "europe_pmc_match",
    "existing_indexed_match",
    "discovery_status",
    "openalex_url",
]


def normalize_space(value: str) -> str:
    return re.sub(r"\s+", " ", value or "").strip()


def strip_accents(value: str) -> str:
    return "".join(ch for ch in unicodedata.normalize("NFKD", value) if not unicodedata.combining(ch))


def normalize_doi(value: str) -> str:
    value = normalize_space(value).casefold()
    value = re.sub(r"^https?://(?:dx\.)?doi\.org/", "", value)
    value = re.sub(r"^doi:\s*", "", value)
    return value.rstrip(" .;,)")


def normalize_pmid(value: str) -> str:
    value = normalize_space(value)
    m = re.search(r"(\d{4,9})", value)
    return m.group(1) if m else ""


def norm_text(value: str) -> str:
    return strip_accents(normalize_space(value).casefold())


def abstract_from_inverted_index(index: dict[str, list[int]] | None) -> str:
    if not index:
        return ""
    positions: list[tuple[int, str]] = []
    for token, poss in index.items():
        for pos in poss or []:
            positions.append((int(pos), token))
    positions.sort()
    return normalize_space(" ".join(token for _, token in positions))


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


def request_json(session: requests.Session, params: dict[str, Any]) -> tuple[dict[str, Any], requests.Response]:
    last_exc: Exception | None = None
    for attempt in range(1, MAX_RETRIES + 1):
        try:
            response = session.get(OPENALEX_URL, params=params, timeout=120)
            if response.status_code == 429 or response.status_code >= 500:
                raise requests.HTTPError(f"HTTP {response.status_code}", response=response)
            response.raise_for_status()
            return response.json(), response
        except Exception as exc:
            last_exc = exc
            if attempt == MAX_RETRIES:
                raise
            time.sleep(min(30.0, 2 ** (attempt - 1)))
    assert last_exc is not None
    raise last_exc


def load_pubmed_pmids() -> set[str]:
    with CANDIDATE_PMIDS.open(encoding="utf-8-sig", newline="") as handle:
        pmids = {row["pmid"].strip() for row in csv.DictReader(handle) if row.get("pmid", "").strip()}
    if len(pmids) != 2767:
        raise RuntimeError(f"Expected 2767 PubMed candidate PMIDs, found {len(pmids)}")
    return pmids


def load_europe_pmc_indexes() -> tuple[set[str], set[str]]:
    pmids: set[str] = set()
    dois: set[str] = set()
    with EUROPE_PMC.open(encoding="utf-8-sig", newline="") as handle:
        for row in csv.DictReader(handle):
            pmid = normalize_pmid(row.get("pmid", ""))
            doi = normalize_doi(row.get("doi", ""))
            if pmid:
                pmids.add(pmid)
            if doi:
                dois.add(doi)
    return pmids, dois


def fetch_pubmed_doi_index(pmids: set[str]) -> set[str]:
    endpoint = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esummary.fcgi"
    ordered = sorted(pmids, key=int)
    dois: set[str] = set()
    for start in range(0, len(ordered), 100):
        batch = ordered[start:start + 100]
        payload = {
            "db": "pubmed",
            "id": ",".join(batch),
            "retmode": "json",
            "tool": "pfild_openalex_supplement",
        }
        response = requests.post(endpoint, data=payload, headers={"User-Agent": USER_AGENT}, timeout=120)
        response.raise_for_status()
        result = response.json()["result"]
        for pmid in batch:
            item = result.get(pmid, {})
            for article_id in item.get("articleids", []) or []:
                if str(article_id.get("idtype", "")).casefold() == "doi":
                    doi = normalize_doi(str(article_id.get("value", "")))
                    if doi:
                        dois.add(doi)
                    break
        time.sleep(0.35)
    return dois


def parse_work(work: dict[str, Any], search_terms: set[str], pubmed_pmids: set[str], pubmed_dois: set[str],
               epmc_pmids: set[str], epmc_dois: set[str]) -> dict[str, Any]:
    ids = work.get("ids") or {}
    doi = normalize_doi(str(ids.get("doi") or work.get("doi") or ""))
    pmid = normalize_pmid(str(ids.get("pmid") or ""))
    title = normalize_space(str(work.get("display_name") or work.get("title") or ""))
    abstract = abstract_from_inverted_index(work.get("abstract_inverted_index"))
    combined = norm_text(title + "\n" + abstract)
    explicit = any(norm_text(term) in combined for term in EXACT_PHRASES)
    acronym = bool(re.search(r"\b(?:pf[- ]?ild|pfild)\b", combined, re.I)) or (
        bool(re.search(r"\bppf\b", combined, re.I))
        and ("interstitial lung" in combined or "pulmonary fibros" in combined)
    )
    work_type = normalize_space(str(work.get("type") or ""))
    authors = []
    for authorship in work.get("authorships") or []:
        author = authorship.get("author") or {}
        name = normalize_space(str(author.get("display_name") or ""))
        if name:
            authors.append(name)
    primary = work.get("primary_location") or {}
    source = primary.get("source") or {}
    oa = work.get("open_access") or {}
    pubmed_match = bool((pmid and pmid in pubmed_pmids) or (doi and doi in pubmed_dois))
    epmc_match = bool((pmid and pmid in epmc_pmids) or (doi and doi in epmc_dois))
    existing = pubmed_match or epmc_match
    return {
        "openalex_id": str(work.get("id") or "").replace("https://openalex.org/", ""),
        "title": title,
        "publication_year": work.get("publication_year") or "",
        "publication_date": work.get("publication_date") or "",
        "work_type": work_type,
        "doi": doi,
        "pmid": pmid,
        "authors": "; ".join(authors),
        "source_name": normalize_space(str(source.get("display_name") or "")),
        "source_type": normalize_space(str(source.get("type") or "")),
        "language": normalize_space(str(work.get("language") or "")),
        "cited_by_count": int(work.get("cited_by_count") or 0),
        "referenced_works_count": len(work.get("referenced_works") or []),
        "is_retracted": bool(work.get("is_retracted")),
        "open_access_status": normalize_space(str(oa.get("oa_status") or "")),
        "search_terms": "; ".join(sorted(search_terms)),
        "explicit_phrase_flag": explicit,
        "acronym_context_flag": acronym,
        "grey_like_type_flag": work_type in GREY_LIKE_TYPES,
        "pubmed_match": pubmed_match,
        "europe_pmc_match": epmc_match,
        "existing_indexed_match": existing,
        "discovery_status": "already_in_pubmed_or_europe_pmc" if existing else "supplementary_candidate",
        "openalex_url": str(work.get("id") or ""),
    }


def main() -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    RAW_DIR.mkdir(parents=True, exist_ok=True)

    pubmed_pmids = load_pubmed_pmids()
    epmc_pmids, epmc_dois = load_europe_pmc_indexes()
    pubmed_dois = fetch_pubmed_doi_index(pubmed_pmids)

    session = requests.Session()
    session.headers.update({
        "User-Agent": USER_AGENT,
        "Accept": "application/json",
    })

    mailto = os.getenv("OPENALEX_MAILTO", "").strip()
    api_key = os.getenv("OPENALEX_API_KEY", "").strip()

    works_by_id: dict[str, dict[str, Any]] = {}
    provenance: defaultdict[str, set[str]] = defaultdict(set)
    request_trace: list[dict[str, Any]] = []
    source_status = "completed"
    blocking_error = ""

    for term_index, term in enumerate(SEARCH_TERMS, start=1):
        cursor = "*"
        for page in range(1, MAX_PAGES_PER_TERM + 1):
            params: dict[str, Any] = {
                "search": term,
                "per-page": PER_PAGE,
                "cursor": cursor,
            }
            if mailto:
                params["mailto"] = mailto
            if api_key:
                params["api_key"] = api_key
            try:
                payload, response = request_json(session, params)
            except requests.HTTPError as exc:
                status = exc.response.status_code if exc.response is not None else None
                source_status = f"blocked_http_{status}" if status else "request_failed"
                blocking_error = repr(exc)
                request_trace.append({
                    "term": term,
                    "term_index": term_index,
                    "page": page,
                    "cursor": cursor,
                    "status": source_status,
                    "error": blocking_error,
                })
                break
            except Exception as exc:
                source_status = "request_failed"
                blocking_error = repr(exc)
                request_trace.append({
                    "term": term,
                    "term_index": term_index,
                    "page": page,
                    "cursor": cursor,
                    "status": source_status,
                    "error": blocking_error,
                })
                break

            raw = response.content
            raw_path = RAW_DIR / f"openalex_term_{term_index:02d}_page_{page:03d}.json.gz"
            with gzip.open(raw_path, "wb") as handle:
                handle.write(raw)
            results = payload.get("results") or []
            meta = payload.get("meta") or {}
            request_trace.append({
                "term": term,
                "term_index": term_index,
                "page": page,
                "cursor": cursor,
                "results": len(results),
                "count": meta.get("count"),
                "next_cursor": meta.get("next_cursor"),
                "request_url": response.url,
                "raw_file": raw_path.name,
                "raw_sha256": sha256_bytes(raw),
                "http_status": response.status_code,
            })

            for work in results:
                work_id = str(work.get("id") or "")
                if not work_id:
                    continue
                if work_id not in works_by_id:
                    works_by_id[work_id] = work
                provenance[work_id].add(term)

            next_cursor = meta.get("next_cursor")
            if not results or not next_cursor or next_cursor == cursor:
                break
            cursor = str(next_cursor)
            time.sleep(REQUEST_DELAY)

        if source_status != "completed":
            break

    records: list[dict[str, Any]] = []
    for work_id, work in works_by_id.items():
        records.append(
            parse_work(
                work,
                provenance[work_id],
                pubmed_pmids,
                pubmed_dois,
                epmc_pmids,
                epmc_dois,
            )
        )

    records.sort(key=lambda r: (
        r["discovery_status"] != "supplementary_candidate",
        not r["explicit_phrase_flag"],
        not r["acronym_context_flag"],
        str(r["publication_year"]),
        r["title"].casefold(),
    ))

    write_csv(OUTPUT_DIR / "openalex_records.csv", records, FIELDS)
    write_jsonl(OUTPUT_DIR / "openalex_records.jsonl", records)
    write_json(OUTPUT_DIR / "openalex_request_trace.json", request_trace)
    write_json(OUTPUT_DIR / "openalex_search_terms.json", {
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "source": "OpenAlex Works API",
        "search_terms": SEARCH_TERMS,
        "type_restrictions": None,
        "date_restrictions": None,
        "language_restrictions": None,
        "api_key_supplied": bool(api_key),
        "human_eligibility_decisions_created": 0,
        "prisma_decisions_created": 0,
    })

    new_records = [r for r in records if r["discovery_status"] == "supplementary_candidate"]
    grey_new = [r for r in new_records if r["grey_like_type_flag"]]
    summary = {
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "status": source_status,
        "blocking_error": blocking_error,
        "queries_executed": len(SEARCH_TERMS) if source_status == "completed" else len({x.get("term") for x in request_trace}),
        "unique_openalex_works": len(records),
        "matched_existing_pubmed_or_europe_pmc": sum(r["existing_indexed_match"] for r in records),
        "supplementary_candidates": len(new_records),
        "supplementary_candidates_with_explicit_phrase": sum(r["explicit_phrase_flag"] for r in new_records),
        "supplementary_candidates_with_acronym_context": sum(r["acronym_context_flag"] for r in new_records),
        "supplementary_grey_like_candidates": len(grey_new),
        "all_type_counts": dict(Counter(r["work_type"] or "unknown" for r in records)),
        "supplementary_type_counts": dict(Counter(r["work_type"] or "unknown" for r in new_records)),
        "grey_like_type_counts": dict(Counter(r["work_type"] or "unknown" for r in grey_new)),
        "records_without_pmid": sum(not r["pmid"] for r in records),
        "records_without_doi": sum(not r["doi"] for r in records),
        "human_eligibility_decisions_created": 0,
        "prisma_decisions_created": 0,
    }
    write_json(OUTPUT_DIR / "openalex_summary.json", summary)
    print(json.dumps(summary, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
