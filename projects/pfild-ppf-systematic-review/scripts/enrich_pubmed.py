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

EUTILS = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi"
TOOL_NAME = "pfild_ppf_systematic_review"
BATCH_SIZE = int(os.getenv("PUBMED_BATCH_SIZE", "100"))
NCBI_API_KEY = os.getenv("NCBI_API_KEY", "").strip()
NCBI_EMAIL = os.getenv("NCBI_EMAIL", "").strip()
REQUEST_DELAY = 0.11 if NCBI_API_KEY else 0.36
MAX_RETRIES = 6

CSV_FIELDS = [
    "import_rank",
    "pmid",
    "title",
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
    if element is None:
        return ""
    return normalize_space("".join(element.itertext()))


def first_text(parent: ET.Element, path: str) -> str:
    return text_content(parent.find(path))


def iter_batches(items: list[str], size: int) -> Iterable[list[str]]:
    for start in range(0, len(items), size):
        yield items[start : start + size]


def fetch_xml(pmids: list[str]) -> bytes:
    params: dict[str, str] = {
        "db": "pubmed",
        "id": ",".join(pmids),
        "retmode": "xml",
        "tool": TOOL_NAME,
    }
    if NCBI_API_KEY:
        params["api_key"] = NCBI_API_KEY
    if NCBI_EMAIL:
        params["email"] = NCBI_EMAIL

    data = urllib.parse.urlencode(params).encode("utf-8")
    request = urllib.request.Request(
        EUTILS,
        data=data,
        headers={
            "User-Agent": f"{TOOL_NAME}/1.0 (+https://github.com/joaooz123-png/segundo-cerebro)",
            "Content-Type": "application/x-www-form-urlencoded",
        },
        method="POST",
    )

    for attempt in range(1, MAX_RETRIES + 1):
        try:
            with urllib.request.urlopen(request, timeout=120) as response:
                payload = response.read()
            if not payload:
                raise RuntimeError("NCBI returned an empty response")
            return payload
        except (urllib.error.URLError, urllib.error.HTTPError, TimeoutError, RuntimeError) as exc:
            if attempt == MAX_RETRIES:
                raise
            wait = min(30.0, (2 ** (attempt - 1)) + 0.25)
            print(f"NCBI request failed on attempt {attempt}: {exc}; retrying in {wait:.2f}s", file=sys.stderr)
            time.sleep(wait)
    raise RuntimeError("unreachable")


def parse_date(article: ET.Element) -> tuple[str, str]:
    article_date = article.find(".//Article/ArticleDate")
    pub_date = article.find(".//JournalIssue/PubDate")
    source = article_date if article_date is not None else pub_date
    if source is None:
        return "", ""

    year = first_text(source, "Year")
    month = first_text(source, "Month")
    day = first_text(source, "Day")
    medline_date = first_text(source, "MedlineDate")

    if year:
        parts = [year]
        if month:
            month_map = {
                "Jan": "01", "Feb": "02", "Mar": "03", "Apr": "04", "May": "05", "Jun": "06",
                "Jul": "07", "Aug": "08", "Sep": "09", "Oct": "10", "Nov": "11", "Dec": "12",
            }
            parts.append(month_map.get(month, month.zfill(2)))
            if day:
                parts.append(day.zfill(2))
        return "-".join(parts), year

    if medline_date:
        match = re.search(r"\b(18|19|20)\d{2}\b", medline_date)
        return medline_date, match.group(0) if match else ""
    return "", ""


def parse_authors(article: ET.Element) -> tuple[list[str], list[str]]:
    authors: list[str] = []
    collective: list[str] = []
    for author in article.findall(".//Article/AuthorList/Author"):
        collective_name = first_text(author, "CollectiveName")
        if collective_name:
            collective.append(collective_name)
            authors.append(collective_name)
            continue
        last = first_text(author, "LastName")
        fore = first_text(author, "ForeName")
        initials = first_text(author, "Initials")
        suffix = first_text(author, "Suffix")
        if last:
            display = ", ".join(part for part in (last, fore or initials) if part)
            if suffix:
                display = f"{display} {suffix}"
            authors.append(display)
    return authors, collective


def parse_abstract(article: ET.Element) -> str:
    sections: list[str] = []
    for abstract_text in article.findall(".//Article/Abstract/AbstractText"):
        label = (abstract_text.attrib.get("Label") or abstract_text.attrib.get("NlmCategory") or "").strip()
        body = text_content(abstract_text)
        if not body:
            continue
        sections.append(f"{label}: {body}" if label else body)
    return "\n".join(sections)


def parse_article_ids(article: ET.Element) -> tuple[str, str, str]:
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
            pmcid = value
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
    values: list[str] = []
    for node in article.findall(".//KeywordList/Keyword"):
        value = text_content(node)
        if value:
            values.append(value)
    return "; ".join(values)


def parse_record(article: ET.Element, rank_by_pmid: dict[str, int]) -> dict[str, Any]:
    pmid = first_text(article, ".//MedlineCitation/PMID")
    title = first_text(article, ".//Article/ArticleTitle")
    abstract = parse_abstract(article)
    authors, collective = parse_authors(article)
    publication_date, publication_year = parse_date(article)
    doi, pmcid, other_ids = parse_article_ids(article)

    journal = first_text(article, ".//Article/Journal/Title")
    journal_abbreviation = first_text(article, ".//MedlineJournalInfo/MedlineTA")
    volume = first_text(article, ".//JournalIssue/Volume")
    issue = first_text(article, ".//JournalIssue/Issue")
    pagination = first_text(article, ".//Article/Pagination/MedlinePgn")
    elocation = first_text(article, ".//Article/ELocationID")
    pages_or_elocation = pagination or elocation

    languages = [text_content(node) for node in article.findall(".//Article/Language") if text_content(node)]
    pub_types = [text_content(node) for node in article.findall(".//Article/PublicationTypeList/PublicationType") if text_content(node)]
    country = first_text(article, ".//MedlineJournalInfo/Country")
    citation_status = article.find(".//MedlineCitation").attrib.get("Status", "") if article.find(".//MedlineCitation") is not None else ""

    title_lower = title.casefold()
    combined_lower = f"{title}\n{abstract}".casefold()
    explicit_pfild_title = any(term in title_lower for term in PFILD_TERMS)
    explicit_ppf_title = PPF_TERM in title_lower
    explicit_pfild_anywhere = any(term in combined_lower for term in PFILD_TERMS)
    explicit_ppf_anywhere = PPF_TERM in combined_lower
    non_ipf_context = any(term in combined_lower for term in NON_IPF_TERMS)
    ipf_mentioned = "idiopathic pulmonary fibrosis" in combined_lower
    ipf_only_suspected = ipf_mentioned and not non_ipf_context and not explicit_pfild_anywhere and not explicit_ppf_anywhere

    if explicit_pfild_title or explicit_ppf_title:
        priority = "high"
    elif explicit_pfild_anywhere or explicit_ppf_anywhere:
        priority = "medium"
    else:
        priority = "low"

    return {
        "import_rank": rank_by_pmid.get(pmid, ""),
        "pmid": pmid,
        "title": title,
        "abstract": abstract,
        "all_authors": "; ".join(authors),
        "author_count": len(authors),
        "collective_authors": "; ".join(collective),
        "journal": journal,
        "journal_abbreviation": journal_abbreviation,
        "publication_date": publication_date,
        "publication_year": publication_year,
        "volume": volume,
        "issue": issue,
        "pages_or_elocation": pages_or_elocation,
        "doi": doi,
        "pmcid": pmcid,
        "other_article_ids": other_ids,
        "language": "; ".join(languages),
        "publication_types": "; ".join(pub_types),
        "mesh_terms": parse_mesh(article),
        "keywords": parse_keywords(article),
        "country": country,
        "citation_status": citation_status,
        "has_abstract": bool(abstract),
        "explicit_pfild_title": explicit_pfild_title,
        "explicit_ppf_title": explicit_ppf_title,
        "explicit_pfild_anywhere": explicit_pfild_anywhere,
        "explicit_ppf_anywhere": explicit_ppf_anywhere,
        "non_ipf_context_flag": non_ipf_context,
        "ipf_only_suspected_flag": ipf_only_suspected,
        "machine_recall_priority": priority,
        "pubmed_url": f"https://pubmed.ncbi.nlm.nih.gov/{pmid}/" if pmid else "",
    }


def main() -> None:
    state = json.loads(STATE_PATH.read_text(encoding="utf-8"))
    pmids = [str(value) for value in state["pubmed"]["pmids"]]
    if len(pmids) != len(set(pmids)):
        raise RuntimeError("project_state.json contains duplicate PMIDs")

    expected = int(state["prisma"]["identified_imported"])
    if len(pmids) != expected:
        raise RuntimeError(f"PMID count {len(pmids)} does not match PRISMA identified_imported {expected}")

    rank_by_pmid = {pmid: index for index, pmid in enumerate(pmids, start=1)}
    records: dict[str, dict[str, Any]] = {}
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    batches = list(iter_batches(pmids, BATCH_SIZE))
    for batch_number, batch in enumerate(batches, start=1):
        print(f"Fetching PubMed batch {batch_number}/{len(batches)} ({len(batch)} PMIDs)")
        payload = fetch_xml(batch)
        root = ET.fromstring(payload)
        for article in root.findall("PubmedArticle"):
            record = parse_record(article, rank_by_pmid)
            if record["pmid"]:
                records[record["pmid"]] = record
        time.sleep(REQUEST_DELAY)

    ordered_records = [records[pmid] for pmid in pmids if pmid in records]
    missing = [pmid for pmid in pmids if pmid not in records]

    with CSV_PATH.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=CSV_FIELDS, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(ordered_records)

    with JSONL_PATH.open("w", encoding="utf-8") as handle:
        for record in ordered_records:
            handle.write(json.dumps(record, ensure_ascii=False, sort_keys=True) + "\n")

    MISSING_PATH.write_text("\n".join(missing) + ("\n" if missing else ""), encoding="utf-8")

    pmid_hash = hashlib.sha256("\n".join(pmids).encode("utf-8")).hexdigest()
    summary = {
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "source": "NCBI PubMed EFetch",
        "input_project_state": str(STATE_PATH.relative_to(ROOT)),
        "expected_pmids": len(pmids),
        "retrieved_records": len(ordered_records),
        "missing_pmids": len(missing),
        "records_with_abstract": sum(bool(record["has_abstract"]) for record in ordered_records),
        "records_with_doi": sum(bool(record["doi"]) for record in ordered_records),
        "records_with_pmcid": sum(bool(record["pmcid"]) for record in ordered_records),
        "high_recall_priority": sum(record["machine_recall_priority"] == "high" for record in ordered_records),
        "medium_recall_priority": sum(record["machine_recall_priority"] == "medium" for record in ordered_records),
        "low_recall_priority": sum(record["machine_recall_priority"] == "low" for record in ordered_records),
        "pmid_order_sha256": pmid_hash,
        "machine_flags_are_final_decisions": False,
        "notes": [
            "Machine recall flags are prioritization aids only.",
            "No inclusion, exclusion, deduplication, or PRISMA screening count is changed by this script.",
            "Complete authorship is preserved in all_authors; et al. is not applied to source metadata.",
        ],
    }
    SUMMARY_PATH.write_text(json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    print(json.dumps(summary, ensure_ascii=False, indent=2))
    if missing:
        raise RuntimeError(f"NCBI did not return {len(missing)} PMIDs; see {MISSING_PATH}")


if __name__ == "__main__":
    main()
