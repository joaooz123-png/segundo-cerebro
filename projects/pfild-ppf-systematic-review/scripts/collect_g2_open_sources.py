from __future__ import annotations

import csv
import hashlib
import json
import time
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PUBMED_UNION_FILE = ROOT / "data" / "pubmed_v2_validation" / "pubmed_candidate_union_pmids.csv"
OUT = ROOT / "data" / "g2_open_sources"
OUT.mkdir(parents=True, exist_ok=True)

USER_AGENT = "pfild-ppf-systematic-review/1.0 (systematic evidence census)"

EUROPE_PMC_QUERY = """(
  TITLE_ABS:\"progressive fibrosing interstitial lung disease\" OR
  TITLE_ABS:\"progressive fibrosing interstitial lung diseases\" OR
  TITLE_ABS:\"progressive-fibrosing interstitial lung disease\" OR
  TITLE_ABS:\"progressive-fibrosing interstitial lung diseases\" OR
  TITLE_ABS:\"progressive fibrotic interstitial lung disease\" OR
  TITLE_ABS:\"progressive fibrotic interstitial lung diseases\" OR
  TITLE_ABS:\"progressive fibrosing ILD\" OR
  TITLE_ABS:\"progressive fibrotic ILD\" OR
  TITLE_ABS:\"progressive fibrosing phenotype\" OR
  TITLE_ABS:\"progressive fibrotic phenotype\" OR
  TITLE_ABS:\"progressive fibrosis phenotype\" OR
  TITLE_ABS:\"PF-ILD\" OR
  TITLE_ABS:PFILD OR
  TITLE:\"progressive pulmonary fibrosis\" OR
  (
    TITLE_ABS:\"progressive pulmonary fibrosis\" AND
    (
      TITLE_ABS:\"interstitial lung disease\" OR
      TITLE_ABS:\"interstitial lung diseases\" OR
      TITLE_ABS:ILD OR
      TITLE_ABS:\"non-IPF\" OR
      TITLE_ABS:\"non IPF\" OR
      TITLE_ABS:fibrosing OR
      TITLE_ABS:fibrotic
    )
  )
) OR (
  (
    TITLE_ABS:\"fibrosing interstitial lung disease\" OR
    TITLE_ABS:\"fibrosing interstitial lung diseases\" OR
    TITLE_ABS:\"fibrotic interstitial lung disease\" OR
    TITLE_ABS:\"fibrotic interstitial lung diseases\" OR
    TITLE_ABS:\"chronic fibrosing interstitial lung disease\" OR
    TITLE_ABS:\"chronic fibrosing interstitial lung diseases\"
  ) AND (
    TITLE_ABS:progression OR TITLE_ABS:progressive OR TITLE_ABS:progressing OR TITLE_ABS:progressed OR
    TITLE_ABS:\"disease progression\"
  )
)""".strip()

CTGOV_QUERIES = [
    '"progressive fibrosing interstitial lung disease"',
    '"progressive-fibrosing interstitial lung disease"',
    '"progressive fibrotic interstitial lung disease"',
    '"progressive pulmonary fibrosis"',
    '"progressive fibrotic phenotype" AND "interstitial lung disease"',
    'PF-ILD',
    'PFILD',
]

CTGOV_SENTINELS = ["NCT02999178", "NCT03099187", "NCT03858842"]


def request_json(url: str, params: dict[str, object], retries: int = 6) -> dict:
    query = urllib.parse.urlencode(params, doseq=True)
    request = urllib.request.Request(
        f"{url}?{query}",
        headers={"User-Agent": USER_AGENT, "Accept": "application/json"},
    )
    for attempt in range(retries):
        try:
            with urllib.request.urlopen(request, timeout=180) as response:
                return json.loads(response.read().decode("utf-8"))
        except (urllib.error.HTTPError, urllib.error.URLError, TimeoutError):
            if attempt + 1 == retries:
                raise
            time.sleep(min(2 ** attempt, 30))
    raise RuntimeError("Unreachable")


def read_pubmed_union() -> set[str]:
    with PUBMED_UNION_FILE.open(encoding="utf-8-sig", newline="") as handle:
        rows = list(csv.DictReader(handle))
    pmids = {row["pmid"] for row in rows}
    if len(pmids) != 2767:
        raise RuntimeError(f"Expected 2,767 PubMed candidate PMIDs, got {len(pmids)}")
    return pmids


def write_csv(path: Path, headers: list[str], rows: list[list[object]]) -> None:
    with path.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.writer(handle)
        writer.writerow(headers)
        writer.writerows(rows)


def collect_europe_pmc(pubmed_union: set[str]) -> dict:
    endpoint = "https://www.ebi.ac.uk/europepmc/webservices/rest/search"
    cursor = "*"
    records_by_key: dict[str, dict] = {}
    raw_pages = []
    page_number = 0
    hit_count = None

    while cursor:
        page_number += 1
        data = request_json(endpoint, {
            "query": EUROPE_PMC_QUERY,
            "format": "json",
            "resultType": "core",
            "pageSize": 1000,
            "cursorMark": cursor,
        })
        raw_pages.append(data)
        if hit_count is None:
            hit_count = int(data.get("hitCount", 0))
        results = data.get("resultList", {}).get("result", [])
        for record in results:
            source = str(record.get("source") or "")
            record_id = str(record.get("id") or "")
            key = f"{source}:{record_id}"
            records_by_key[key] = record
        next_cursor = data.get("nextCursorMark")
        if not next_cursor or next_cursor == cursor or not results:
            break
        cursor = next_cursor
        time.sleep(0.15)

    records = list(records_by_key.values())
    records.sort(key=lambda row: (
        str(row.get("firstPublicationDate") or row.get("pubYear") or ""),
        str(row.get("source") or ""),
        str(row.get("id") or ""),
    ), reverse=True)

    csv_rows = []
    non_pubmed = []
    source_counts: dict[str, int] = {}
    for rank, row in enumerate(records, 1):
        source = str(row.get("source") or "")
        source_counts[source] = source_counts.get(source, 0) + 1
        pmid = str(row.get("pmid") or "")
        pmcid = str(row.get("pmcid") or "")
        doi = str(row.get("doi") or "")
        in_pubmed_union = bool(pmid and pmid in pubmed_union)
        if not in_pubmed_union:
            non_pubmed.append(row)
        csv_rows.append([
            rank,
            source,
            row.get("id", ""),
            pmid,
            pmcid,
            doi,
            row.get("title", ""),
            row.get("authorString", ""),
            row.get("journalTitle", ""),
            row.get("pubYear", ""),
            row.get("firstPublicationDate", ""),
            row.get("pubType", ""),
            row.get("language", ""),
            row.get("isOpenAccess", ""),
            row.get("inEPMC", ""),
            row.get("inPMC", ""),
            row.get("citedByCount", ""),
            "yes" if in_pubmed_union else "no",
            row.get("fullTextUrlList", {}).get("fullTextUrl", [{}])[0].get("url", "")
            if row.get("fullTextUrlList", {}).get("fullTextUrl") else "",
        ])

    write_csv(
        OUT / "europe_pmc_records.csv",
        [
            "rank", "source", "source_id", "pmid", "pmcid", "doi", "title", "authors",
            "journal", "publication_year", "first_publication_date", "publication_type",
            "language", "open_access", "in_europe_pmc", "in_pmc", "cited_by_count",
            "in_pubmed_candidate_union", "fulltext_url",
        ],
        csv_rows,
    )
    with (OUT / "europe_pmc_records.jsonl").open("w", encoding="utf-8") as handle:
        for row in records:
            handle.write(json.dumps(row, ensure_ascii=False) + "\n")
    (OUT / "europe_pmc_raw_pages.json").write_text(
        json.dumps(raw_pages, ensure_ascii=False), encoding="utf-8"
    )
    (OUT / "europe_pmc_query.txt").write_text(EUROPE_PMC_QUERY + "\n", encoding="utf-8")

    return {
        "submitted_query": EUROPE_PMC_QUERY,
        "reported_hit_count": hit_count,
        "unique_source_records": len(records),
        "source_counts": source_counts,
        "records_with_pmid": sum(bool(row.get("pmid")) for row in records),
        "records_without_pmid": sum(not bool(row.get("pmid")) for row in records),
        "records_not_in_pubmed_candidate_union_by_pmid": len(non_pubmed),
        "pages_retrieved": len(raw_pages),
        "raw_sha256": hashlib.sha256(
            (OUT / "europe_pmc_records.jsonl").read_bytes()
        ).hexdigest(),
    }


def get_nested(mapping: dict, *keys, default=""):
    current = mapping
    for key in keys:
        if not isinstance(current, dict):
            return default
        current = current.get(key)
    return current if current is not None else default


def collect_clinicaltrials() -> dict:
    endpoint = "https://clinicaltrials.gov/api/v2/studies"
    studies_by_nct: dict[str, dict] = {}
    provenance: dict[str, set[str]] = {}
    query_counts: dict[str, int] = {}

    for query in CTGOV_QUERIES:
        token = None
        count = None
        while True:
            params: dict[str, object] = {
                "query.term": query,
                "format": "json",
                "pageSize": 100,
                "countTotal": "true",
            }
            if token:
                params["pageToken"] = token
            data = request_json(endpoint, params)
            if count is None:
                count = int(data.get("totalCount", 0))
                query_counts[query] = count
            for study in data.get("studies", []):
                nct = str(get_nested(study, "protocolSection", "identificationModule", "nctId"))
                if not nct:
                    continue
                studies_by_nct[nct] = study
                provenance.setdefault(nct, set()).add(query)
            token = data.get("nextPageToken")
            if not token:
                break
            time.sleep(0.15)

    studies = [studies_by_nct[nct] for nct in sorted(studies_by_nct)]
    csv_rows = []
    for study in studies:
        protocol = study.get("protocolSection", {})
        identification = protocol.get("identificationModule", {})
        status = protocol.get("statusModule", {})
        design = protocol.get("designModule", {})
        conditions = protocol.get("conditionsModule", {})
        sponsors = protocol.get("sponsorCollaboratorsModule", {})
        arms = protocol.get("armsInterventionsModule", {})
        nct = str(identification.get("nctId") or "")
        interventions = []
        for item in arms.get("interventions", []) or []:
            interventions.append(f"{item.get('type', '')}: {item.get('name', '')}".strip(": "))
        csv_rows.append([
            nct,
            identification.get("briefTitle", ""),
            identification.get("officialTitle", ""),
            design.get("studyType", ""),
            "; ".join(design.get("phases", []) or []),
            status.get("overallStatus", ""),
            get_nested(status, "startDateStruct", "date"),
            get_nested(status, "completionDateStruct", "date"),
            "; ".join(conditions.get("conditions", []) or []),
            "; ".join(interventions),
            get_nested(sponsors, "leadSponsor", "name"),
            "; ".join(sorted(provenance.get(nct, set()))),
            f"https://clinicaltrials.gov/study/{nct}",
        ])

    write_csv(
        OUT / "clinicaltrials_gov_records.csv",
        [
            "nct_id", "brief_title", "official_title", "study_type", "phases", "overall_status",
            "start_date", "completion_date", "conditions", "interventions", "lead_sponsor",
            "matched_queries", "source_url",
        ],
        csv_rows,
    )
    with (OUT / "clinicaltrials_gov_records.jsonl").open("w", encoding="utf-8") as handle:
        for study in studies:
            handle.write(json.dumps(study, ensure_ascii=False) + "\n")
    (OUT / "clinicaltrials_gov_queries.json").write_text(
        json.dumps({"queries": CTGOV_QUERIES, "query_counts": query_counts}, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    found_sentinels = [nct for nct in CTGOV_SENTINELS if nct in studies_by_nct]
    return {
        "queries": CTGOV_QUERIES,
        "query_counts_before_union": query_counts,
        "unique_nct_records_after_union": len(studies),
        "sentinel_nct_ids": CTGOV_SENTINELS,
        "sentinels_retrieved": found_sentinels,
        "sentinels_missing": [nct for nct in CTGOV_SENTINELS if nct not in studies_by_nct],
        "raw_sha256": hashlib.sha256(
            (OUT / "clinicaltrials_gov_records.jsonl").read_bytes()
        ).hexdigest(),
    }


def main() -> None:
    pubmed_union = read_pubmed_union()
    europe_pmc = collect_europe_pmc(pubmed_union)
    clinicaltrials = collect_clinicaltrials()
    summary = {
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "gate": "G2 source coverage",
        "status": "partial — two open sources executed; no completeness claim",
        "europe_pmc": europe_pmc,
        "clinicaltrials_gov": clinicaltrials,
        "governance": {
            "eligibility_decisions_made": 0,
            "prisma_counts_changed": False,
            "cross_source_deduplication_status": "candidate identifiers only; formal G3 deduplication pending",
        },
    }
    (OUT / "g2_open_sources_summary.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    print(json.dumps(summary, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
