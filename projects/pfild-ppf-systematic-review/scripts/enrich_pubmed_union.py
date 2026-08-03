from __future__ import annotations

import csv
import gzip
import hashlib
import json
import os
import re
import time
from collections import Counter, defaultdict
from difflib import SequenceMatcher
from pathlib import Path
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from enrich_pubmed import (
    CSV_FIELDS,
    REQUEST_DELAY,
    batches,
    fetch_summary,
    fetch_xml,
    parse_article,
    parse_summary_item,
)

ROOT = Path(__file__).resolve().parents[1]
CANDIDATE_PATH = ROOT / "data" / "pubmed_v2_validation" / "pubmed_candidate_union_pmids.csv"
EUROPE_PMC_PATH = ROOT / "data" / "g2_open_sources" / "europe_pmc_records.csv"
CTGOV_PATH = ROOT / "data" / "g2_open_sources" / "clinicaltrials_gov_records.csv"
OUTPUT_DIR = Path(os.getenv("PFILD_OUTPUT_DIR", ROOT / "artifacts" / "pubmed_union_enrichment"))
RAW_DIR = OUTPUT_DIR / "raw_efetch_xml_gz"
CT_RAW_DIR = OUTPUT_DIR / "clinicaltrials_gov_missing_raw"
BATCH_SIZE = int(os.getenv("PUBMED_UNION_BATCH_SIZE", "100"))
CT_DELAY = float(os.getenv("CTGOV_REQUEST_DELAY", "0.20"))

REGISTRY_PATTERNS = {
    "NCT": re.compile(r"\bNCT\d{8}\b", re.I),
    "EudraCT": re.compile(r"\b(?:EUCTR)?\d{4}-\d{6}-\d{2}(?:-[A-Z]{2})?\b", re.I),
    "ChiCTR": re.compile(r"\bChiCTR[A-Z0-9-]{6,}\b", re.I),
    "jRCT": re.compile(r"\bjRCT[a-zA-Z0-9-]{6,}\b", re.I),
    "UMIN": re.compile(r"\bUMIN(?:000)?\d{6,}\b", re.I),
    "DRKS": re.compile(r"\bDRKS\d{8}\b", re.I),
    "ISRCTN": re.compile(r"\bISRCTN\d{8}\b", re.I),
}


def normalize_space(value: str) -> str:
    return re.sub(r"\s+", " ", value or "").strip()


def normalize_doi(value: str) -> str:
    value = normalize_space(value).lower()
    value = re.sub(r"^https?://(?:dx\.)?doi\.org/", "", value)
    value = re.sub(r"^doi:\s*", "", value)
    return value.rstrip(" .;")


def normalize_title(value: str) -> str:
    value = normalize_space(value).casefold()
    value = re.sub(r"<[^>]+>", " ", value)
    value = re.sub(r"[^a-z0-9]+", " ", value)
    return normalize_space(value)


def token_set(value: str) -> set[str]:
    return {token for token in normalize_title(value).split() if len(token) > 2}


def title_scores(a: str, b: str) -> tuple[float, float]:
    na, nb = normalize_title(a), normalize_title(b)
    if not na or not nb:
        return 0.0, 0.0
    seq = SequenceMatcher(None, na, nb).ratio()
    ta, tb = token_set(a), token_set(b)
    jac = len(ta & tb) / len(ta | tb) if ta and tb else 0.0
    return seq, jac


def first_author_surname(authors: str) -> str:
    first = normalize_space(authors).split(";")[0].split(",")[0].strip()
    return re.sub(r"[^a-z0-9]", "", first.casefold())


def sha256_text(lines: list[str]) -> str:
    return hashlib.sha256("\n".join(lines).encode("utf-8")).hexdigest()


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


def fetch_ctgov(nct_id: str) -> dict[str, Any]:
    url = f"https://clinicaltrials.gov/api/v2/studies/{nct_id}"
    request = Request(
        url,
        headers={"User-Agent": "pfild_ppf_systematic_review/1.3 (+https://github.com/joaooz123-png/segundo-cerebro)"},
    )
    for attempt in range(1, 6):
        try:
            with urlopen(request, timeout=90) as response:
                return json.loads(response.read().decode("utf-8"))
        except (HTTPError, URLError, TimeoutError, json.JSONDecodeError):
            if attempt == 5:
                raise
            time.sleep(min(20, 2 ** (attempt - 1)))
    raise RuntimeError("unreachable")


def flatten_ctgov(study: dict[str, Any]) -> dict[str, Any]:
    protocol = study.get("protocolSection", {})
    identification = protocol.get("identificationModule", {})
    status = protocol.get("statusModule", {})
    design = protocol.get("designModule", {})
    conditions = protocol.get("conditionsModule", {})
    arms = protocol.get("armsInterventionsModule", {})
    sponsor = protocol.get("sponsorCollaboratorsModule", {})
    interventions = []
    for item in arms.get("interventions", []) or []:
        interventions.append(f"{item.get('type', '')}: {item.get('name', '')}".strip(": "))
    return {
        "nct_id": identification.get("nctId", ""),
        "brief_title": identification.get("briefTitle", ""),
        "official_title": identification.get("officialTitle", ""),
        "acronym": identification.get("acronym", ""),
        "overall_status": status.get("overallStatus", ""),
        "start_date": (status.get("startDateStruct") or {}).get("date", ""),
        "completion_date": (status.get("completionDateStruct") or {}).get("date", ""),
        "study_type": design.get("studyType", ""),
        "phases": "; ".join(design.get("phases", []) or []),
        "enrollment": (design.get("enrollmentInfo") or {}).get("count", ""),
        "conditions": "; ".join(conditions.get("conditions", []) or []),
        "interventions": "; ".join(interventions),
        "lead_sponsor": (sponsor.get("leadSponsor") or {}).get("name", ""),
        "has_results": bool(study.get("resultsSection")),
        "source_url": f"https://clinicaltrials.gov/study/{identification.get('nctId', '')}",
    }


def extract_registry_mentions(record: dict[str, Any]) -> list[dict[str, str]]:
    text = "\n".join(
        str(record.get(field, ""))
        for field in ("title", "abstract", "other_article_ids", "keywords")
    )
    found: list[dict[str, str]] = []
    seen: set[tuple[str, str]] = set()
    for registry_type, pattern in REGISTRY_PATTERNS.items():
        for match in pattern.findall(text):
            identifier = match.upper() if registry_type in {"NCT", "DRKS", "ISRCTN"} else match
            key = (registry_type, identifier)
            if key not in seen:
                seen.add(key)
                found.append({
                    "pmid": str(record.get("pmid", "")),
                    "title": str(record.get("title", "")),
                    "registry_type": registry_type,
                    "registry_id": identifier,
                    "link_basis": "explicit identifier in PubMed metadata",
                    "pubmed_url": str(record.get("pubmed_url", "")),
                })
    return found


def enrich_pubmed() -> tuple[list[dict[str, Any]], list[dict[str, str]]]:
    candidates = read_csv(CANDIDATE_PATH)
    pmids = [row["pmid"].strip() for row in candidates if row.get("pmid", "").strip()]
    if len(pmids) != len(set(pmids)):
        raise RuntimeError("Candidate PMID list contains duplicates")
    rank_by_pmid = {row["pmid"].strip(): int(row["rank"]) for row in candidates}
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    RAW_DIR.mkdir(parents=True, exist_ok=True)

    records_by_pmid: dict[str, dict[str, Any]] = {}
    raw_manifest: list[dict[str, Any]] = []
    for index, batch in enumerate(batches(pmids, BATCH_SIZE), start=1):
        raw = fetch_xml(batch)
        raw_path = RAW_DIR / f"efetch_{index:03d}.xml.gz"
        with gzip.open(raw_path, "wb") as handle:
            handle.write(raw)
        raw_manifest.append({
            "batch": index,
            "requested_pmids": len(batch),
            "first_pmid": batch[0],
            "last_pmid": batch[-1],
            "compressed_file": raw_path.name,
            "raw_sha256": hashlib.sha256(raw).hexdigest(),
        })
        import xml.etree.ElementTree as ET
        root = ET.fromstring(raw)
        for article in root.findall(".//PubmedArticle"):
            record = parse_article(article, rank_by_pmid)
            if record.get("pmid"):
                records_by_pmid[str(record["pmid"])] = record
        for book in root.findall(".//PubmedBookArticle"):
            record = parse_article(book, rank_by_pmid)
            if record.get("pmid"):
                records_by_pmid[str(record["pmid"])] = record
        time.sleep(REQUEST_DELAY)

    missing = [pmid for pmid in pmids if pmid not in records_by_pmid]
    summary_raw: dict[str, Any] = {}
    if missing:
        for batch in batches(missing, BATCH_SIZE):
            result = fetch_summary(batch)
            for pmid in batch:
                item = result.get(pmid)
                if item:
                    records_by_pmid[pmid] = parse_summary_item(pmid, item, rank_by_pmid)
                    summary_raw[pmid] = item
            time.sleep(REQUEST_DELAY)

    ordered = [records_by_pmid[pmid] for pmid in pmids if pmid in records_by_pmid]
    still_missing = [pmid for pmid in pmids if pmid not in records_by_pmid]
    write_csv(OUTPUT_DIR / "pubmed_union_metadata.csv", ordered, CSV_FIELDS)
    with (OUTPUT_DIR / "pubmed_union_metadata.jsonl").open("w", encoding="utf-8") as handle:
        for row in ordered:
            handle.write(json.dumps(row, ensure_ascii=False) + "\n")
    write_json(OUTPUT_DIR / "raw_batch_manifest.json", raw_manifest)
    write_json(OUTPUT_DIR / "esummary_fallback_raw.json", summary_raw)
    (OUTPUT_DIR / "pubmed_union_missing_pmids.txt").write_text("\n".join(still_missing), encoding="utf-8")
    return ordered, candidates


def boundary_dedup(pubmed_rows: list[dict[str, Any]]) -> dict[str, Any]:
    epmc_rows = read_csv(EUROPE_PMC_PATH)
    pubmed_by_pmid = {str(r["pmid"]): r for r in pubmed_rows}
    exact_pmid_pairs: list[dict[str, Any]] = []
    doi_groups: list[dict[str, Any]] = []
    boundary_pairs: list[dict[str, Any]] = []
    non_pubmed_epmc = []

    for ep in epmc_rows:
        pmid = ep.get("pmid", "").strip()
        doi = normalize_doi(ep.get("doi", ""))
        if pmid and pmid in pubmed_by_pmid:
            pub = pubmed_by_pmid[pmid]
            exact_pmid_pairs.append({
                "cluster_key": f"PMID:{pmid}",
                "pmid": pmid,
                "pubmed_title": pub.get("title", ""),
                "europe_pmc_source": ep.get("source", ""),
                "europe_pmc_source_id": ep.get("source_id", ""),
                "europe_pmc_title": ep.get("title", ""),
                "doi": doi,
                "recommended_action": "collapse source representation; preserve both provenance records",
                "confidence": "exact",
            })
        else:
            non_pubmed_epmc.append(ep)

    doi_map: dict[str, list[dict[str, str]]] = defaultdict(list)
    for row in pubmed_rows:
        doi = normalize_doi(str(row.get("doi", "")))
        if doi:
            doi_map[doi].append({
                "source": "PubMed", "source_id": str(row.get("pmid", "")),
                "pmid": str(row.get("pmid", "")), "title": str(row.get("title", "")),
                "authors": str(row.get("all_authors", "")), "year": str(row.get("publication_year", "")),
                "publication_type": str(row.get("publication_types", "")),
            })
    for ep in epmc_rows:
        doi = normalize_doi(ep.get("doi", ""))
        if doi:
            doi_map[doi].append({
                "source": f"EuropePMC:{ep.get('source', '')}", "source_id": ep.get("source_id", ""),
                "pmid": ep.get("pmid", ""), "title": ep.get("title", ""),
                "authors": ep.get("authors", ""), "year": ep.get("publication_year", ""),
                "publication_type": ep.get("publication_type", ""),
            })
    for doi, members in sorted(doi_map.items()):
        unique_reports = {(m["pmid"], normalize_title(m["title"]), m["source"]) for m in members}
        if len(unique_reports) < 2:
            continue
        unique_titles = {normalize_title(m["title"]) for m in members if normalize_title(m["title"])}
        unique_pmids = {m["pmid"] for m in members if m["pmid"]}
        if len(unique_pmids) == 1:
            classification = "same_report_multiple_source_representations"
            action = "collapse source representations only"
        elif len(unique_titles) == 1:
            classification = "same_doi_same_title_review_required"
            action = "manual verification before any merge"
        else:
            classification = "doi_collision_distinct_reports"
            action = "never merge by DOI alone; retain all reports"
        for m in members:
            doi_groups.append({
                "doi": doi, "classification": classification, **m,
                "recommended_action": action,
            })

    for ep in non_pubmed_epmc:
        best: list[tuple[float, float, dict[str, Any]]] = []
        ep_year = str(ep.get("publication_year", ""))
        ep_first = first_author_surname(ep.get("authors", ""))
        ep_doi = normalize_doi(ep.get("doi", ""))
        for pub in pubmed_rows:
            pub_year = str(pub.get("publication_year", ""))
            doi_equal = bool(ep_doi and ep_doi == normalize_doi(str(pub.get("doi", ""))))
            if ep_year.isdigit() and pub_year.isdigit() and abs(int(ep_year) - int(pub_year)) > 2 and not doi_equal:
                continue
            seq, jac = title_scores(ep.get("title", ""), str(pub.get("title", "")))
            if max(seq, jac) < 0.78 and not doi_equal:
                continue
            best.append((max(seq, jac), jac, pub))
        best.sort(key=lambda item: (item[0], item[1]), reverse=True)
        for rank, (seq_score, jac_score, pub) in enumerate(best[:5], start=1):
            pub_first = first_author_surname(str(pub.get("all_authors", "")))
            doi_equal = bool(ep_doi and ep_doi == normalize_doi(str(pub.get("doi", ""))))
            exact_title = normalize_title(ep.get("title", "")) == normalize_title(str(pub.get("title", "")))
            author_support = bool(ep_first and pub_first and ep_first == pub_first)
            ep_source = ep.get("source", "")
            if doi_equal and exact_title:
                classification = "exact_duplicate_candidate"
                action = "verify version/source; collapse representation only if same report"
            elif ep_source == "PPR" and max(seq_score, jac_score) >= 0.84:
                classification = "preprint_published_family_candidate"
                action = "retain both reports; link within one publication family after confirmation"
            elif exact_title or (max(seq_score, jac_score) >= 0.94 and author_support):
                classification = "same_report_or_family_candidate"
                action = "manual boundary review; do not merge automatically"
            elif max(seq_score, jac_score) >= 0.86:
                classification = "similar_title_review_candidate"
                action = "manual review for family relationship or distinct report"
            else:
                classification = "weak_similarity_context_only"
                action = "retain separately unless human review finds a relationship"
            boundary_pairs.append({
                "europe_pmc_source": ep_source,
                "europe_pmc_source_id": ep.get("source_id", ""),
                "europe_pmc_pmid": ep.get("pmid", ""),
                "europe_pmc_doi": ep_doi,
                "europe_pmc_title": ep.get("title", ""),
                "europe_pmc_year": ep_year,
                "pubmed_pmid": pub.get("pmid", ""),
                "pubmed_doi": normalize_doi(str(pub.get("doi", ""))),
                "pubmed_title": pub.get("title", ""),
                "pubmed_year": pub.get("publication_year", ""),
                "candidate_rank": rank,
                "sequence_similarity": round(seq_score, 4),
                "token_jaccard": round(jac_score, 4),
                "doi_equal": doi_equal,
                "first_author_support": author_support,
                "classification": classification,
                "recommended_action": action,
                "human_status": "not reviewed",
            })

    exact_fields = list(exact_pmid_pairs[0].keys()) if exact_pmid_pairs else [
        "cluster_key", "pmid", "pubmed_title", "europe_pmc_source", "europe_pmc_source_id",
        "europe_pmc_title", "doi", "recommended_action", "confidence",
    ]
    doi_fields = list(doi_groups[0].keys()) if doi_groups else [
        "doi", "classification", "source", "source_id", "pmid", "title", "authors",
        "year", "publication_type", "recommended_action",
    ]
    boundary_fields = list(boundary_pairs[0].keys()) if boundary_pairs else []
    write_csv(OUTPUT_DIR / "exact_source_duplicates_by_pmid_v2.csv", exact_pmid_pairs, exact_fields)
    write_csv(OUTPUT_DIR / "doi_groups_full_union.csv", doi_groups, doi_fields)
    if boundary_fields:
        write_csv(OUTPUT_DIR / "boundary_candidate_pairs.csv", boundary_pairs, boundary_fields)

    return {
        "europe_pmc_records": len(epmc_rows),
        "exact_pmid_source_duplicates": len(exact_pmid_pairs),
        "europe_pmc_without_matching_pmid": len(non_pubmed_epmc),
        "doi_group_rows": len(doi_groups),
        "doi_collision_groups": len({r["doi"] for r in doi_groups if r["classification"] == "doi_collision_distinct_reports"}),
        "boundary_candidate_pairs": len(boundary_pairs),
        "boundary_class_counts": dict(Counter(r["classification"] for r in boundary_pairs)),
        "non_pubmed_epmc_with_no_candidate_above_threshold": len({
            ep["source_id"] for ep in non_pubmed_epmc
        } - {
            r["europe_pmc_source_id"] for r in boundary_pairs
        }),
    }


def recover_registry_records(pubmed_rows: list[dict[str, Any]]) -> dict[str, Any]:
    mentions = []
    for row in pubmed_rows:
        mentions.extend(extract_registry_mentions(row))
    mention_fields = ["pmid", "title", "registry_type", "registry_id", "link_basis", "pubmed_url"]
    write_csv(OUTPUT_DIR / "publication_registry_mentions.csv", mentions, mention_fields)

    current_ct = read_csv(CTGOV_PATH)
    current_ncts = {row.get("nct_id", "").upper() for row in current_ct if row.get("nct_id", "")}
    mentioned_ncts = sorted({m["registry_id"].upper() for m in mentions if m["registry_type"] == "NCT"})
    missing_ncts = sorted(set(mentioned_ncts) - current_ncts)
    CT_RAW_DIR.mkdir(parents=True, exist_ok=True)
    recovered = []
    failures = []
    for nct_id in missing_ncts:
        try:
            study = fetch_ctgov(nct_id)
            write_json(CT_RAW_DIR / f"{nct_id}.json", study)
            recovered.append(flatten_ctgov(study))
        except Exception as exc:
            failures.append({"nct_id": nct_id, "error": repr(exc)})
        time.sleep(CT_DELAY)
    fields = [
        "nct_id", "brief_title", "official_title", "acronym", "overall_status",
        "start_date", "completion_date", "study_type", "phases", "enrollment",
        "conditions", "interventions", "lead_sponsor", "has_results", "source_url",
    ]
    write_csv(OUTPUT_DIR / "clinicaltrials_gov_recovered_from_publications.csv", recovered, fields)
    write_csv(OUTPUT_DIR / "clinicaltrials_gov_recovery_failures.csv", failures, ["nct_id", "error"])
    return {
        "registry_mentions_total": len(mentions),
        "registry_type_counts": dict(Counter(m["registry_type"] for m in mentions)),
        "unique_nct_mentions": len(mentioned_ncts),
        "ncts_already_in_current_set": len(set(mentioned_ncts) & current_ncts),
        "ncts_missing_from_current_set": len(missing_ncts),
        "ncts_recovered": len(recovered),
        "nct_recovery_failures": len(failures),
    }


def main() -> None:
    pubmed_rows, candidates = enrich_pubmed()
    boundary_summary = boundary_dedup(pubmed_rows)
    registry_summary = recover_registry_records(pubmed_rows)
    pmids = [str(row["pmid"]) for row in pubmed_rows]
    status_counts = Counter(str(row.get("metadata_retrieval_status", "")) for row in pubmed_rows)
    summary = {
        "generated_at_utc": __import__("datetime").datetime.now(__import__("datetime").timezone.utc).isoformat(),
        "input_candidate_pmids": len(candidates),
        "metadata_rows": len(pubmed_rows),
        "unique_pmids": len(set(pmids)),
        "pmid_order_sha256": sha256_text(pmids),
        "metadata_status_counts": dict(status_counts),
        "records_with_abstract": sum(bool(row.get("abstract")) for row in pubmed_rows),
        "records_with_doi": sum(bool(row.get("doi")) for row in pubmed_rows),
        "records_with_pmcid": sum(bool(row.get("pmcid")) for row in pubmed_rows),
        "boundary_deduplication": boundary_summary,
        "registry_recovery": registry_summary,
        "prisma_decisions_created": 0,
        "human_eligibility_decisions_created": 0,
    }
    write_json(OUTPUT_DIR / "pubmed_union_enrichment_boundary_summary.json", summary)
    if len(pubmed_rows) != len(candidates):
        raise RuntimeError(f"Metadata coverage incomplete: {len(pubmed_rows)} of {len(candidates)}")
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
