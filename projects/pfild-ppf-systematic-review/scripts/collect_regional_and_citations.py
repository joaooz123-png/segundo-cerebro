from __future__ import annotations

import csv
import gzip
import hashlib
import json
import re
import time
import unicodedata
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from urllib.parse import urlencode, urljoin

import requests
from bs4 import BeautifulSoup

ROOT = Path(__file__).resolve().parents[1]
SENTINELS = ROOT / "data" / "pubmed_v2_validation" / "pubmed_v2_sentinel_validation.csv"
UNION_PMIDS = ROOT / "data" / "pubmed_v2_validation" / "pubmed_candidate_union_pmids.csv"
OUTPUT = ROOT / "artifacts" / "g2_regional_citations"
RAW = OUTPUT / "raw"

EMAIL = "joaorenno96@gmail.com"
USER_AGENT = "pfild_ppf_systematic_review/1.4 (+https://github.com/joaooz123-png/segundo-cerebro)"
SESSION = requests.Session()
SESSION.headers.update({"User-Agent": USER_AGENT, "Accept-Language": "en,pt-BR;q=0.9,es;q=0.8"})

TERMS = [
    '"progressive pulmonary fibrosis"',
    '"progressive fibrosing interstitial lung disease"',
    '"progressive fibrotic interstitial lung disease"',
    '"progressive fibrosing interstitial lung diseases"',
    '"fibrosis pulmonar progresiva"',
    '"enfermedad pulmonar intersticial fibrosante progresiva"',
    '"fibrose pulmonar progressiva"',
    '"doença pulmonar intersticial fibrosante progressiva"',
    '"doenca pulmonar intersticial fibrosante progressiva"',
    'PF-ILD',
    'PFILD',
    'DPI-FP',
]

DIRECT_TERMS = (
    "progressive pulmonary fibrosis",
    "progressive fibrosing interstitial lung disease",
    "progressive fibrotic interstitial lung disease",
    "progressive fibrosing interstitial lung diseases",
    "progressive fibrotic interstitial lung diseases",
    "fibrosis pulmonar progresiva",
    "enfermedad pulmonar intersticial fibrosante progresiva",
    "fibrose pulmonar progressiva",
    "doença pulmonar intersticial fibrosante progressiva",
    "doenca pulmonar intersticial fibrosante progressiva",
    "pf-ild",
    "pfild",
    "dpi-fp",
)

DOI_RE = re.compile(r"10\.\d{4,9}/[-._;()/:A-Z0-9]+", re.I)
BVS_ID_RE = re.compile(r"\b(?:biblio-\d+|lil-\d+|mdl(?:bvsreg\.sh-)?\d+|mdlbvsreg\.sh-\d+)\b", re.I)
YEAR_RE = re.compile(r"\b(?:18|19|20)\d{2}\b")


def normalize_space(value: str) -> str:
    return re.sub(r"\s+", " ", value or "").strip()


def normalize_key(value: str) -> str:
    value = unicodedata.normalize("NFKD", value or "").encode("ascii", "ignore").decode("ascii")
    value = re.sub(r"[^a-z0-9]+", " ", value.casefold())
    return normalize_space(value)


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle))


def write_csv(path: Path, rows: list[dict[str, Any]], fields: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2), encoding="utf-8")


def get(url: str, params: dict[str, Any] | None = None, timeout: int = 90) -> requests.Response:
    for attempt in range(1, 6):
        try:
            response = SESSION.get(url, params=params, timeout=timeout)
            if response.status_code in {429, 500, 502, 503, 504}:
                raise requests.HTTPError(f"transient {response.status_code}")
            response.raise_for_status()
            return response
        except (requests.RequestException, requests.HTTPError):
            if attempt == 5:
                raise
            time.sleep(min(20, 2 ** (attempt - 1)))
    raise RuntimeError("unreachable")


def relevance_flags(title: str, text: str = "") -> dict[str, Any]:
    title_n = normalize_key(title)
    all_n = normalize_key(title + " " + text)
    title_hit = any(normalize_key(term) in title_n for term in DIRECT_TERMS)
    anywhere_hit = any(normalize_key(term) in all_n for term in DIRECT_TERMS)
    return {
        "direct_term_title": title_hit,
        "direct_term_anywhere": anywhere_hit,
        "machine_priority": "high" if title_hit else "medium" if anywhere_hit else "low",
    }


def save_raw(path: Path, content: bytes) -> str:
    path.parent.mkdir(parents=True, exist_ok=True)
    with gzip.open(path, "wb") as handle:
        handle.write(content)
    return hashlib.sha256(content).hexdigest()


def best_title(block: Any) -> str:
    selectors = ["h1", "h2", "h3", "h4", ".title", ".record-title", ".item-title"]
    for selector in selectors:
        node = block.select_one(selector)
        if node:
            value = normalize_space(node.get_text(" ", strip=True))
            if len(value) >= 12:
                return value
    for link in block.select("a[href]"):
        value = normalize_space(link.get_text(" ", strip=True))
        if len(value) >= 25:
            return value
    return ""


def best_url(block: Any, base_url: str) -> str:
    for link in block.select("a[href]"):
        text = normalize_space(link.get_text(" ", strip=True))
        href = link.get("href", "")
        if len(text) >= 12 and href and not href.startswith("javascript:"):
            return urljoin(base_url, href)
    return ""


def parse_bvs(html: str, query: str, page: int, request_url: str) -> list[dict[str, Any]]:
    soup = BeautifulSoup(html, "html.parser")
    candidate_blocks = soup.select("div.result-item, div.record, div.item, article, li.result")
    if not candidate_blocks:
        candidate_blocks = [node.parent for node in soup.find_all(string=BVS_ID_RE) if node.parent]
    rows: list[dict[str, Any]] = []
    seen_nodes: set[int] = set()
    for block in candidate_blocks:
        if id(block) in seen_nodes:
            continue
        seen_nodes.add(id(block))
        text = normalize_space(block.get_text(" ", strip=True))
        match = BVS_ID_RE.search(text)
        if not match:
            continue
        record_id = match.group(0)
        title = best_title(block)
        if not title:
            before = text[: match.start()].strip(" -|:")
            title = before[-500:]
        doi_match = DOI_RE.search(text)
        year_match = YEAR_RE.search(text)
        flags = relevance_flags(title, text)
        rows.append({
            "source": "BVS",
            "record_id": record_id,
            "title": title,
            "year": year_match.group(0) if year_match else "",
            "doi": doi_match.group(0).rstrip(".,;)") if doi_match else "",
            "databases": "; ".join(sorted(set(re.findall(r"\b(?:LILACS|MEDLINE|BINACIS|UNISALUD|IBECS|BDENF|CUMED|PAHO)\b", text, re.I)))),
            "snippet": text[:4000],
            "query": query,
            "page": page,
            "record_url": best_url(block, request_url),
            "request_url": request_url,
            **flags,
        })
    return rows


def parse_scielo(html: str, query: str, page: int, request_url: str) -> list[dict[str, Any]]:
    soup = BeautifulSoup(html, "html.parser")
    candidate_blocks = soup.select("div.item, div.result, div.search-result, article, li.item")
    rows: list[dict[str, Any]] = []
    for block in candidate_blocks:
        text = normalize_space(block.get_text(" ", strip=True))
        title = best_title(block)
        url = best_url(block, request_url)
        doi_match = DOI_RE.search(text)
        if not title or ("scielo" not in url.casefold() and not doi_match):
            continue
        year_match = YEAR_RE.search(text)
        flags = relevance_flags(title, text)
        identifier = doi_match.group(0).rstrip(".,;)") if doi_match else url
        rows.append({
            "source": "SciELO",
            "record_id": identifier,
            "title": title,
            "year": year_match.group(0) if year_match else "",
            "doi": doi_match.group(0).rstrip(".,;)") if doi_match else "",
            "snippet": text[:4000],
            "query": query,
            "page": page,
            "record_url": url,
            "request_url": request_url,
            **flags,
        })
    return rows


def deduplicate_records(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    merged: dict[str, dict[str, Any]] = {}
    for row in rows:
        key = row.get("doi", "").casefold() or row.get("record_id", "").casefold() or normalize_key(row.get("title", ""))
        if not key:
            continue
        if key not in merged:
            row["matched_queries"] = row.pop("query", "")
            row["matched_pages"] = str(row.pop("page", ""))
            merged[key] = row
        else:
            current = merged[key]
            queries = set(filter(None, current.get("matched_queries", "").split(" || ")))
            queries.add(row.get("query", ""))
            pages = set(filter(None, current.get("matched_pages", "").split(";")))
            pages.add(str(row.get("page", "")))
            current["matched_queries"] = " || ".join(sorted(queries))
            current["matched_pages"] = ";".join(sorted(pages))
            current["direct_term_title"] = bool(current.get("direct_term_title")) or bool(row.get("direct_term_title"))
            current["direct_term_anywhere"] = bool(current.get("direct_term_anywhere")) or bool(row.get("direct_term_anywhere"))
            if current["direct_term_title"]:
                current["machine_priority"] = "high"
            elif current["direct_term_anywhere"]:
                current["machine_priority"] = "medium"
    return sorted(merged.values(), key=lambda row: (row.get("machine_priority", "z"), row.get("year", ""), row.get("title", "")), reverse=True)


def collect_regional() -> dict[str, Any]:
    bvs_rows: list[dict[str, Any]] = []
    scielo_rows: list[dict[str, Any]] = []
    requests_log: list[dict[str, Any]] = []
    for source, base_url in [("BVS", "https://pesquisa.bvsalud.org/portal/"), ("SciELO", "https://search.scielo.org/")]:
        for query_index, query in enumerate(TERMS, start=1):
            previous_ids: set[str] = set()
            for page in range(1, 6):
                params = {"q": query, "page": page}
                if source == "BVS":
                    params["lang"] = "en"
                else:
                    params["where"] = "ORG"
                try:
                    response = get(base_url, params=params)
                    request_url = response.url
                    digest = save_raw(RAW / source.casefold() / f"q{query_index:02d}_p{page:02d}.html.gz", response.content)
                    parsed = parse_bvs(response.text, query, page, request_url) if source == "BVS" else parse_scielo(response.text, query, page, request_url)
                    ids = {row["record_id"] for row in parsed if row.get("record_id")}
                    requests_log.append({
                        "source": source, "query": query, "page": page, "url": request_url,
                        "status": response.status_code, "bytes": len(response.content),
                        "parsed_records": len(parsed), "raw_sha256": digest,
                    })
                    if source == "BVS":
                        bvs_rows.extend(parsed)
                    else:
                        scielo_rows.extend(parsed)
                    if not ids or ids <= previous_ids:
                        break
                    previous_ids |= ids
                    time.sleep(0.35)
                except Exception as exc:
                    requests_log.append({
                        "source": source, "query": query, "page": page,
                        "url": base_url + "?" + urlencode(params), "status": "failed",
                        "bytes": 0, "parsed_records": 0, "raw_sha256": "", "error": repr(exc),
                    })
                    break
    bvs_unique = deduplicate_records(bvs_rows)
    scielo_unique = deduplicate_records(scielo_rows)
    regional_fields = [
        "source", "record_id", "title", "year", "doi", "databases", "snippet",
        "matched_queries", "matched_pages", "record_url", "request_url",
        "direct_term_title", "direct_term_anywhere", "machine_priority",
    ]
    write_csv(OUTPUT / "bvs_lilacs_records.csv", bvs_unique, regional_fields)
    write_csv(OUTPUT / "scielo_records.csv", scielo_unique, regional_fields)
    write_json(OUTPUT / "regional_requests_log.json", requests_log)
    return {
        "bvs_unique_records": len(bvs_unique),
        "scielo_unique_records": len(scielo_unique),
        "bvs_priority_counts": dict(Counter(row["machine_priority"] for row in bvs_unique)),
        "scielo_priority_counts": dict(Counter(row["machine_priority"] for row in scielo_unique)),
        "requests_succeeded": sum(row.get("status") == 200 for row in requests_log),
        "requests_failed": sum(row.get("status") == "failed" for row in requests_log),
    }


def epmc_list(source: str, ext_id: str, relation: str) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    all_rows: list[dict[str, Any]] = []
    manifest: list[dict[str, Any]] = []
    page = 1
    while True:
        url = f"https://www.ebi.ac.uk/europepmc/webservices/rest/{source}/{ext_id}/{relation}"
        response = get(url, {"format": "json", "pageSize": 1000, "page": page, "email": EMAIL})
        digest = save_raw(RAW / "europe_pmc_citations" / f"{source}_{ext_id}_{relation}_p{page}.json.gz", response.content)
        payload = response.json()
        list_key = "referenceList" if relation == "references" else "citationList"
        item_key = "reference" if relation == "references" else "citation"
        container = payload.get(list_key) or {}
        items = container.get(item_key) or []
        if isinstance(items, dict):
            items = [items]
        all_rows.extend(items)
        hit_count = int(payload.get("hitCount") or container.get("hitCount") or len(items))
        manifest.append({
            "source": source, "ext_id": ext_id, "relation": relation, "page": page,
            "items": len(items), "hit_count": hit_count, "raw_sha256": digest,
        })
        if not items or page * 1000 >= hit_count:
            break
        page += 1
        time.sleep(0.15)
    return all_rows, manifest


def flatten_epmc(item: dict[str, Any], seed: dict[str, str], relation: str) -> dict[str, Any]:
    title = normalize_space(str(item.get("title") or item.get("articleTitle") or ""))
    abstract = normalize_space(str(item.get("abstractText") or ""))
    source = str(item.get("source") or item.get("src") or "")
    ext_id = str(item.get("id") or item.get("extId") or item.get("pmid") or item.get("pmcid") or "")
    flags = relevance_flags(title, abstract)
    return {
        "seed_id": seed.get("seed_id", ""),
        "seed_pmid": seed.get("pmid", ""),
        "seed_title": seed.get("title", ""),
        "relation": relation,
        "source": source,
        "source_id": ext_id,
        "pmid": str(item.get("pmid") or (ext_id if source == "MED" and ext_id.isdigit() else "")),
        "pmcid": str(item.get("pmcid") or ""),
        "doi": str(item.get("doi") or ""),
        "title": title,
        "authors": str(item.get("authorString") or ""),
        "journal": str(item.get("journalAbbreviation") or item.get("journalTitle") or ""),
        "year": str(item.get("pubYear") or ""),
        "cited_by_count": item.get("citedByCount", ""),
        **flags,
    }


def collect_citations() -> dict[str, Any]:
    sentinels = [row for row in read_csv(SENTINELS) if row.get("pmid", "").isdigit()]
    union_pmids = {row["pmid"] for row in read_csv(UNION_PMIDS)}
    edges: list[dict[str, Any]] = []
    manifest: list[dict[str, Any]] = []
    failures: list[dict[str, str]] = []
    for seed in sentinels:
        for relation in ("references", "citations"):
            try:
                items, pages = epmc_list("MED", seed["pmid"], relation)
                manifest.extend(pages)
                for item in items:
                    row = flatten_epmc(item, seed, relation)
                    row["in_pubmed_candidate_union"] = bool(row["pmid"] and row["pmid"] in union_pmids)
                    edges.append(row)
            except Exception as exc:
                failures.append({"seed_id": seed.get("seed_id", ""), "pmid": seed["pmid"], "relation": relation, "error": repr(exc)})
            time.sleep(0.15)

    edge_fields = [
        "seed_id", "seed_pmid", "seed_title", "relation", "source", "source_id",
        "pmid", "pmcid", "doi", "title", "authors", "journal", "year", "cited_by_count",
        "direct_term_title", "direct_term_anywhere", "machine_priority", "in_pubmed_candidate_union",
    ]
    write_csv(OUTPUT / "sentinel_citation_edges.csv", edges, edge_fields)
    write_json(OUTPUT / "sentinel_citation_manifest.json", manifest)
    write_csv(OUTPUT / "sentinel_citation_failures.csv", failures, ["seed_id", "pmid", "relation", "error"])

    candidates: dict[str, dict[str, Any]] = {}
    for row in edges:
        if row["in_pubmed_candidate_union"]:
            continue
        key = row["pmid"] or row["doi"].casefold() or f"{row['source']}:{row['source_id']}" or normalize_key(row["title"])
        if not key:
            continue
        if key not in candidates:
            candidates[key] = {
                "source": row["source"], "source_id": row["source_id"], "pmid": row["pmid"],
                "pmcid": row["pmcid"], "doi": row["doi"], "title": row["title"],
                "authors": row["authors"], "journal": row["journal"], "year": row["year"],
                "relations": {row["relation"]}, "seed_pmids": {row["seed_pmid"]},
                "seed_ids": {row["seed_id"]}, "direct_term_title": row["direct_term_title"],
                "direct_term_anywhere": row["direct_term_anywhere"], "machine_priority": row["machine_priority"],
                "human_status": "not screened",
            }
        else:
            current = candidates[key]
            current["relations"].add(row["relation"])
            current["seed_pmids"].add(row["seed_pmid"])
            current["seed_ids"].add(row["seed_id"])
            current["direct_term_title"] = current["direct_term_title"] or row["direct_term_title"]
            current["direct_term_anywhere"] = current["direct_term_anywhere"] or row["direct_term_anywhere"]
            current["machine_priority"] = "high" if current["direct_term_title"] else "medium" if current["direct_term_anywhere"] else "low"
    candidate_rows = []
    for row in candidates.values():
        row["relations"] = "; ".join(sorted(row["relations"]))
        row["seed_pmids"] = "; ".join(sorted(row["seed_pmids"]))
        row["seed_ids"] = "; ".join(sorted(row["seed_ids"]))
        candidate_rows.append(row)
    candidate_rows.sort(key=lambda row: ({"high": 0, "medium": 1, "low": 2}.get(row["machine_priority"], 9), -len(row["seed_ids"].split(";")), row["title"]))
    candidate_fields = [
        "source", "source_id", "pmid", "pmcid", "doi", "title", "authors", "journal", "year",
        "relations", "seed_pmids", "seed_ids", "direct_term_title", "direct_term_anywhere",
        "machine_priority", "human_status",
    ]
    write_csv(OUTPUT / "sentinel_citation_candidates_outside_union.csv", candidate_rows, candidate_fields)
    return {
        "sentinels_attempted": len(sentinels),
        "citation_edges": len(edges),
        "reference_edges": sum(row["relation"] == "references" for row in edges),
        "citing_edges": sum(row["relation"] == "citations" for row in edges),
        "unique_candidates_outside_union": len(candidate_rows),
        "candidate_priority_counts": dict(Counter(row["machine_priority"] for row in candidate_rows)),
        "failures": len(failures),
    }


def main() -> None:
    OUTPUT.mkdir(parents=True, exist_ok=True)
    regional = collect_regional()
    citations = collect_citations()
    summary = {
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "queries": TERMS,
        "regional": regional,
        "citation_chasing": citations,
        "method_notes": [
            "Regional HTML is preserved verbatim in gzip files with SHA-256 digests.",
            "Europe PMC references and citations endpoints were used for the 62 PubMed-applicable sentinels.",
            "Candidates are not eligibility decisions and do not change PRISMA counts.",
            "Europe PMC citation coverage is based on open citation data and is not equivalent to Scopus or Web of Science.",
        ],
        "human_eligibility_decisions_created": 0,
        "prisma_counts_changed": False,
    }
    write_json(OUTPUT / "g2_regional_citations_summary.json", summary)
    print(json.dumps(summary, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
