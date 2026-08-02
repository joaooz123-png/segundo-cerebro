from __future__ import annotations

import csv
import hashlib
import json
import os
import re
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable

ROOT = Path(__file__).resolve().parents[1]
STATE_PATH = ROOT / "data" / "project_state.json"
OUTPUT_DIR = ROOT / "data" / "pubmed"
CSV_PATH = OUTPUT_DIR / "pubmed_metadata.csv"
JSONL_PATH = OUTPUT_DIR / "pubmed_metadata.jsonl"
SUMMARY_PATH = OUTPUT_DIR / "pubmed_enrichment_summary.json"
MISSING_PATH = OUTPUT_DIR / "pubmed_missing_pmids.txt"

EUTILS_FETCH = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi"
EUTILS_SUMMARY = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esummary.fcgi"
TOOL_NAME = "pfild_ppf_systematic_review"
BATCH_SIZE = int(os.getenv("PUBMED_BATCH_SIZE", "100"))
NCBI_API_KEY = os.getenv("NCBI_API_KEY", "").strip()
NCBI_EMAIL = os.getenv("NCBI_EMAIL", "").strip()
REQUEST_DELAY = 0.11 if NCBI_API_KEY else 0.36
MAX_RETRIES = 6

CSV_FIELDS = [
    "import_rank",
    "pmid",
    "metadata_retrieval_status",
    "metadata_source",
    "title",
    "vernacular_title",
    "abstract",
    "all_authors",
    "author_count",
    "collective_authors",
    "journal",
    "journal_abbreviation",
    "publication_date",
    "publication_year",
    "volume",
    "issue",
    "pages_or_elocation",
    "doi",
    "pmcid",
    "other_article_ids",
    "language",
    "publication_types",
    "mesh_terms",
    "keywords",
    "country",
    "citation_status",
    "has_abstract",
    "explicit_pfild_title",
    "explicit_ppf_title",
    "explicit_pfild_anywhere",
    "explicit_ppf_anywhere",
    "non_ipf_context_flag",
    "ipf_only_suspected_flag",
    "machine_recall_priority",
    "pubmed_url",
]

PFILD_TERMS = (
    "progressive fibrosing interstitial lung disease",
    "progressive-fibrosing interstitial lung disease",
    "progressive fibrotic interstitial lung disease",
    "progressive fibrosing ild",
    "progressive fibrotic ild",
    "progressive fibrotic phenotype",
    "progressive fibrosis phenotype",
    "pf-ild",
    "pfild",
)
PPF_TERM = "progressive pulmonary fibrosis"
NON_IPF_TERMS = (
    "non-ipf",
    "non ipf",
    "other than idiopathic pulmonary fibrosis",
    "excluding idiopathic pulmonary fibrosis",
    "connective tissue disease",
    "systemic autoimmune",
    "hypersensitivity pneumonitis",
    "unclassifiable interstitial lung disease",
    "sarcoidosis",
    "occupational interstitial",
)


def normalize_space(value: str) -> str:
    return re.sub(r"\s+", " ", value or "").strip()


def text_content(element: ET.Element | None) -> str:
    return normalize_space("".join(element.itertext())) if element is not None else ""


def first_text(parent: ET.Element, path: str) -> str:
    return text_content(parent.find(path))


def batches(items: list[str], size: int) -> Iterable[list[str]]:
    for start in range(0, len(items), size):
        yield items[start : start + size]


def request_bytes(endpoint: str, params: dict[str, str]) -> bytes:
    payload = dict(params)
    payload["tool"] = TOOL_NAME
    if NCBI_API_KEY:
        payload["api_key"] = NCBI_API_KEY
    if NCBI_EMAIL:
        payload["email"] = NCBI_EMAIL
    data = urllib.parse.urlencode(payload).encode("utf-8")
    request = urllib.request.Request(
        endpoint,
        data=data,
        headers={
            "User-Agent": f"{TOOL_NAME}/1.1 (+https://github.com/joaooz123-png/segundo-cerebro)",
            "Content-Type": "application/x-www-form-urlencoded",
        },
        method="POST",
    )
    for attempt in range(1, MAX_RETRIES + 1):
        try:
            with urllib.request.urlopen(request, timeout=120) as response:
                result = response.read()
            if not result:
                raise RuntimeError("NCBI returned an empty response")
            return result
        except (urllib.error.URLError, urllib.error.HTTPError, TimeoutError, RuntimeError) as exc:
            if attempt == MAX_RETRIES:
                raise
            wait = min(30.0, (2 ** (attempt - 1)) + 0.25)
            print(f"NCBI request failed on attempt {attempt}: {exc}; retrying in {wait:.2f}s", file=sys.stderr)
            time.sleep(wait)
    raise RuntimeError("unreachable")


def fetch_xml(pmids: list[str]) -> bytes:
    return request_bytes(EUTILS_FETCH, {"db": "pubmed", "id": ",".join(pmids), "retmode": "xml"})


def fetch_summary(pmids: list[str]) -> dict[str, Any]:
    raw = request_bytes(EUTILS_SUMMARY, {"db": "pubmed", "id": ",".join(pmids), "retmode": "json"})
    return json.loads(raw.decode("utf-8"))["result"]


def parse_date(article: ET.Element) -> tuple[str, str]:
    source = article.find(".//Article/ArticleDate") or article.find(".//JournalIssue/PubDate")
    if source is None:
        return "", ""
    year = first_text(source, "Year")
    month = first_text(source, "Month")
    day = first_text(source, "Day")
    medline_date = first_text(source, "MedlineDate")
    if year:
        month_map = {
            "Jan": "01", "Feb": "02", "Mar": "03", "Apr": "04", "May": "05", "Jun": "06",
            "Jul": "07", "Aug": "08", "Sep": "09", "Oct": "10", "Nov": "11", "Dec": "12",
        }
        parts = [year]
        if month:
            parts.append(month_map.get(month, month.zfill(2)))
            if day:
                parts.append(day.zfill(2))
        return "-".join(parts), year
    match = re.search(r"\b(?:18|19|20)\d{2}\b", medline_date)
    return medline_date, match.group(0) if match else ""


def parse_authors(article: ET.Element) -> tuple[list[str], list[str]]:
    authors: list[str] = []
    collective: list[str] = []
    for author in article.findall(".//Article/AuthorList/Author"):
        group = first_text(author, "CollectiveName")
        if group:
            collective.append(group)
            authors.append(group)
            continue
        last = first_text(author, "LastName")
        fore = first_text(author, "ForeName") or first_text(author, "Initials")
        suffix = first_text(author, "Suffix")
        if last:
            display = ", ".join(value for value in (last, fore) if value)
            authors.append(f"{display} {suffix}".strip())
    return authors, collective


def parse_abstract(article: ET.Element) -> str:
    sections: list[str] = []
    for node in article.findall(".//Article/Abstract/AbstractText"):
        body = text_content(node)
        if not body:
            continue
        label = (node.attrib.get("Label") or node.attrib.get("NlmCategory") or "").strip()
        sections.append(f"{label}: {body}" if label else body)
    return "\n".join(sections)


def parse_ids(article: ET.Element) -> tuple[str, str, str]:
    doi = ""
    pmcid = ""
    others: list[str] = []
    for node in article.findall(".//PubmedData/ArticleIdList/ArticleId"):
        id_type = (node.attrib.get("IdType") or "other").lower()
        value = text_content(node)
        if not value:
            continue
        if id_type == "doi":
            doi = value
        elif id_type in {"pmc", "pmcid"}:
            pmcid = value.replace("pmc-id:", "").replace(";", "").strip()
        elif id_type != "pubmed":
            others.append(f"{id_type}:{value}")
    return doi, pmcid, "; ".join(others)


def parse_mesh(article: ET.Element) -> str:
    terms: list[str] = []
    for heading in article.findall(".//MeshHeadingList/MeshHeading"):
        descriptor = first_text(heading, "DescriptorName")
        qualifiers = [text_content(node) for node in heading.findall("QualifierName") if text_content(node)]
        if descriptor:
            terms.append(f"{descriptor} / {' / '.join(qualifiers)}" if qualifiers else descriptor)
    return "; ".join(terms)


def parse_keywords(article: ET.Element) -> str:
    return "; ".join(text_content(node) for node in article.findall(".//KeywordList/Keyword") if text_content(node))


def apply_machine_flags(record: dict[str, Any]) -> dict[str, Any]:
    title_lower = str(record.get("title", "")).casefold()
    combined_lower = f"{record.get('title', '')}\n{record.get('abstract', '')}".casefold()
    pfild_title = any(term in title_lower for term in PFILD_TERMS)
    ppf_title = PPF_TERM in title_lower
    pfild_any = any(term in combined_lower for term in PFILD_TERMS)
    ppf_any = PPF_TERM in combined_lower
    non_ipf = any(term in combined_lower for term in NON_IPF_TERMS)
    ipf_only = "idiopathic pulmonary fibrosis" in combined_lower and not non_ipf and not pfild_any and not ppf_any
    priority = "high" if pfild_title or ppf_title else "medium" if pfild_any or ppf_any else "low"
    record.update(
        {
            "explicit_pfild_title": pfild_title,
            "explicit_ppf_title": ppf_title,
            "explicit_pfild_anywhere": pfild_any,
            "explicit_ppf_anywhere": ppf_any,
            "non_ipf_context_flag": non_ipf,
            "ipf_only_suspected_flag": ipf_only,
            "machine_recall_priority": priority,
        }
    )
    return record


def parse_article(article: ET.Element, rank_by_pmid: dict[str, int]) -> dict[str, Any]:
    pmid = first_text(article, ".//MedlineCitation/PMID")
    authors, collective = parse_authors(article)
    publication_date, publication_year = parse_date(article)
    doi, pmcid, other_ids = parse_ids(article)
    abstract = parse_abstract(article)
    medline = article.find(".//MedlineCitation")
    record: dict[str, Any] = {
        "import_rank": rank_by_pmid.get(pmid, ""),
        "pmid": pmid,
        "metadata_retrieval_status": "complete",
        "metadata_source": "NCBI PubMed EFetch XML",
        "title": first_text(article, ".//Article/ArticleTitle"),
        "vernacular_title": first_text(article, ".//MedlineCitation/OtherAbstract/AbstractText"),
        "abstract": abstract,
        "all_authors": "; ".join(authors),
        "author_count": len(authors),
        "collective_authors": "; ".join(collective),
        "journal": first_text(article, ".//Article/Journal/Title"),
        "journal_abbreviation": first_text(article, ".//MedlineJournalInfo/MedlineTA"),
        "publication_date": publication_date,
        "publication_year": publication_year,
        "volume": first_text(article, ".//JournalIssue/Volume"),
        "issue": first_text(article, ".//JournalIssue/Issue"),
        "pages_or_elocation": first_text(article, ".//Article/Pagination/MedlinePgn") or first_text(article, ".//Article/ELocationID"),
        "doi": doi,
        "pmcid": pmcid,
        "other_article_ids": other_ids,
        "language": "; ".join(text_content(node) for node in article.findall(".//Article/Language") if text_content(node)),
        "publication_types": "; ".join(text_content(node) for node in article.findall(".//Article/PublicationTypeList/PublicationType") if text_content(node)),
        "mesh_terms": parse_mesh(article),
        "keywords": parse_keywords(article),
        "country": first_text(article, ".//MedlineJournalInfo/Country"),
        "citation_status": medline.attrib.get("Status", "") if medline is not None else "",
        "has_abstract": bool(abstract),
        "pubmed_url": f"https://pubmed.ncbi.nlm.nih.gov/{pmid}/",
    }
    return apply_machine_flags(record)


def summary_ids(item: dict[str, Any]) -> tuple[str, str, str]:
    doi = ""
    pmcid = ""
    others: list[str] = []
    for entry in item.get("articleids", []) or []:
        id_type = str(entry.get("idtype", "other")).lower()
        value = str(entry.get("value", "")).strip()
        if id_type == "doi":
            doi = value
        elif id_type in {"pmc", "pmcid"}:
            pmcid = value.replace("pmc-id:", "").replace(";", "").strip()
        elif id_type != "pubmed" and value:
            others.append(f"{id_type}:{value}")
    return doi, pmcid, "; ".join(others)


def parse_summary_item(pmid: str, item: dict[str, Any], rank_by_pmid: dict[str, int]) -> dict[str, Any]:
    doi, pmcid, other_ids = summary_ids(item)
    authors = [str(author.get("name", "")).strip() for author in item.get("authors", []) if author.get("name")]
    pubdate = str(item.get("pubdate", "")).strip()
    year_match = re.search(r"\b(?:18|19|20)\d{2}\b", pubdate)
    record: dict[str, Any] = {
        "import_rank": rank_by_pmid.get(pmid, ""),
        "pmid": pmid,
        "metadata_retrieval_status": "summary_only",
        "metadata_source": "NCBI PubMed ESummary JSON fallback",
        "title": normalize_space(str(item.get("title", ""))),
        "vernacular_title": normalize_space(str(item.get("vernaculartitle", ""))),
        "abstract": "",
        "all_authors": "; ".join(authors),
        "author_count": len(authors),
        "collective_authors": "; ".join(author for author in authors if "investigator" in author.casefold() or "group" in author.casefold()),
        "journal": str(item.get("fulljournalname", "")),
        "journal_abbreviation": str(item.get("source", "")),
        "publication_date": pubdate,
        "publication_year": year_match.group(0) if year_match else "",
        "volume": str(item.get("volume", "")),
        "issue": str(item.get("issue", "")),
        "pages_or_elocation": str(item.get("pages", "")) or str(item.get("elocationid", "")),
        "doi": doi,
        "pmcid": pmcid,
        "other_article_ids": other_ids,
        "language": "; ".join(item.get("lang", []) or []),
        "publication_types": "; ".join(item.get("pubtype", []) or []),
        "mesh_terms": "",
        "keywords": "",
        "country": "",
        "citation_status": str(item.get("recordstatus", "")),
        "has_abstract": "Has Abstract" in (item.get("attributes", []) or []),
        "pubmed_url": f"https://pubmed.ncbi.nlm.nih.gov/{pmid}/",
    }
    return apply_machine_flags(record)


def unavailable_record(pmid: str, rank_by_pmid: dict[str, int]) -> dict[str, Any]:
    record = {field: "" for field in CSV_FIELDS}
    record.update(
        {
            "import_rank": rank_by_pmid[pmid],
            "pmid": pmid,
            "metadata_retrieval_status": "unavailable",
            "metadata_source": "NCBI returned no EFetch or ESummary record",
            "author_count": 0,
            "has_abstract": False,
            "pubmed_url": f"https://pubmed.ncbi.nlm.nih.gov/{pmid}/",
        }
    )
    return apply_machine_flags(record)


def main() -> None:
    state = json.loads(STATE_PATH.read_text(encoding="utf-8"))
    pmids = [str(value) for value in state["pubmed"]["pmids"]]
    if len(pmids) != len(set(pmids)):
        raise RuntimeError("project_state.json contains duplicate PMIDs")
    expected = int(state["prisma"]["identified_imported"])
    if len(pmids) != expected:
        raise RuntimeError(f"PMID count {len(pmids)} does not match PRISMA identified_imported {expected}")

    rank_by_pmid = {pmid: rank for rank, pmid in enumerate(pmids, start=1)}
    records: dict[str, dict[str, Any]] = {}
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    all_batches = list(batches(pmids, BATCH_SIZE))
    for number, batch in enumerate(all_batches, start=1):
        print(f"Fetching PubMed EFetch batch {number}/{len(all_batches)} ({len(batch)} PMIDs)")
        root = ET.fromstring(fetch_xml(batch))
        for article in root.findall("PubmedArticle"):
            record = parse_article(article, rank_by_pmid)
            if record["pmid"]:
                records[record["pmid"]] = record
        time.sleep(REQUEST_DELAY)

    efetch_missing = [pmid for pmid in pmids if pmid not in records]
    if efetch_missing:
        print(f"Using ESummary fallback for {len(efetch_missing)} PMIDs")
        for batch in batches(efetch_missing, BATCH_SIZE):
            result = fetch_summary(batch)
            for pmid in batch:
                item = result.get(pmid)
                if isinstance(item, dict):
                    records[pmid] = parse_summary_item(pmid, item, rank_by_pmid)
            time.sleep(REQUEST_DELAY)

    unavailable = [pmid for pmid in pmids if pmid not in records]
    for pmid in unavailable:
        records[pmid] = unavailable_record(pmid, rank_by_pmid)

    ordered = [records[pmid] for pmid in pmids]
    if len(ordered) != expected or len({record["pmid"] for record in ordered}) != expected:
        raise RuntimeError("Output does not preserve exactly one row per formal PMID")

    with CSV_PATH.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=CSV_FIELDS, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(ordered)
    with JSONL_PATH.open("w", encoding="utf-8") as handle:
        for record in ordered:
            handle.write(json.dumps(record, ensure_ascii=False, sort_keys=True) + "\n")
    MISSING_PATH.write_text("\n".join(unavailable) + ("\n" if unavailable else ""), encoding="utf-8")

    summary = {
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "source": "NCBI PubMed EFetch with ESummary fallback",
        "input_project_state": str(STATE_PATH.relative_to(ROOT)),
        "expected_pmids": expected,
        "output_rows": len(ordered),
        "complete_efetch_records": sum(record["metadata_retrieval_status"] == "complete" for record in ordered),
        "summary_fallback_records": sum(record["metadata_retrieval_status"] == "summary_only" for record in ordered),
        "unavailable_records": len(unavailable),
        "records_with_abstract": sum(bool(record["abstract"]) for record in ordered),
        "records_with_doi": sum(bool(record["doi"]) for record in ordered),
        "records_with_pmcid": sum(bool(record["pmcid"]) for record in ordered),
        "high_recall_priority": sum(record["machine_recall_priority"] == "high" for record in ordered),
        "medium_recall_priority": sum(record["machine_recall_priority"] == "medium" for record in ordered),
        "low_recall_priority": sum(record["machine_recall_priority"] == "low" for record in ordered),
        "pmid_order_sha256": hashlib.sha256("\n".join(pmids).encode("utf-8")).hexdigest(),
        "machine_flags_are_final_decisions": False,
        "notes": [
            "Every formal PMID is retained as exactly one output row.",
            "ESummary fallback records are explicitly distinguished from complete EFetch records.",
            "Machine recall flags are prioritization aids only.",
            "No inclusion, exclusion, duplicate, or PRISMA screening count is changed.",
            "Complete authorship is preserved when returned by NCBI; et al. is not applied to source metadata.",
        ],
    }
    SUMMARY_PATH.write_text(json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(summary, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
