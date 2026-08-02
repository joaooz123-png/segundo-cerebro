from __future__ import annotations

import csv
import hashlib
import json
import os
import random
import re
import time
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SEARCH_FILE = ROOT / "search" / "pubmed_v2_candidate.txt"
STATE_FILE = ROOT / "data" / "project_state.json"
SEED_DIR = ROOT / "data" / "seeds"
OUT = ROOT / "data" / "pubmed_v2_validation"
OUT.mkdir(parents=True, exist_ok=True)

BASE = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/"
EMAIL = os.getenv("NCBI_EMAIL", "pfild-review@example.invalid")
API_KEY = os.getenv("NCBI_API_KEY", "").strip()
TOOL = "pfild_ppf_systematic_review"


def read_query() -> str:
    lines = []
    for line in SEARCH_FILE.read_text(encoding="utf-8").splitlines():
        if line.lstrip().startswith("#"):
            continue
        lines.append(line)
    query = "\n".join(lines).strip()
    if not query:
        raise RuntimeError("Candidate query is empty")
    return query


def request_json(endpoint: str, params: dict[str, str], retries: int = 6) -> dict:
    payload = dict(params)
    payload.update({"tool": TOOL, "email": EMAIL})
    if API_KEY:
        payload["api_key"] = API_KEY
    data = urllib.parse.urlencode(payload).encode("utf-8")
    req = urllib.request.Request(
        BASE + endpoint,
        data=data,
        headers={"User-Agent": f"{TOOL}/1.0 ({EMAIL})"},
        method="POST",
    )
    for attempt in range(retries):
        try:
            with urllib.request.urlopen(req, timeout=120) as response:
                return json.loads(response.read().decode("utf-8"))
        except (urllib.error.URLError, urllib.error.HTTPError, TimeoutError) as exc:
            if attempt + 1 == retries:
                raise
            time.sleep(min(2 ** attempt, 30))
    raise RuntimeError("Unreachable")


def chunked(items: list[str], size: int):
    for start in range(0, len(items), size):
        yield items[start:start + size]


def load_v1_pmids() -> list[str]:
    state = json.loads(STATE_FILE.read_text(encoding="utf-8"))
    pmids = [str(x) for x in state["pubmed"]["pmids"]]
    if len(pmids) != 1004 or len(set(pmids)) != 1004:
        raise RuntimeError("PubMed v1 state is not the expected 1,004 unique PMIDs")
    return pmids


def load_sentinels() -> list[dict]:
    result = []
    for path in sorted(SEED_DIR.glob("seeds-*.json")):
        for row in json.loads(path.read_text(encoding="utf-8")):
            value = str(row.get("pmid_or_registry") or "").strip()
            if re.fullmatch(r"\d{7,9}", value):
                result.append({
                    "seed_id": row.get("seed_id"),
                    "pmid": value,
                    "title": row.get("title"),
                    "doi": row.get("doi"),
                    "document_type": row.get("document_type"),
                })
    unique = {row["pmid"]: row for row in result}
    return sorted(unique.values(), key=lambda row: row["seed_id"])


def esummary(pmids: list[str]) -> dict[str, dict]:
    records: dict[str, dict] = {}
    for batch in chunked(pmids, 100):
        data = request_json("esummary.fcgi", {
            "db": "pubmed",
            "retmode": "json",
            "id": ",".join(batch),
        })
        result = data.get("result", {})
        for pmid in batch:
            if pmid in result:
                records[pmid] = result[pmid]
        time.sleep(0.12 if API_KEY else 0.36)
    return records


def write_csv(path: Path, headers: list[str], rows: list[list[object]]) -> None:
    with path.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.writer(handle)
        writer.writerow(headers)
        writer.writerows(rows)


def main() -> None:
    query = read_query()
    v1 = load_v1_pmids()
    v1_set = set(v1)
    sentinels = load_sentinels()

    first = request_json("esearch.fcgi", {
        "db": "pubmed",
        "retmode": "json",
        "retmax": "0",
        "term": query,
    })
    first_result = first["esearchresult"]
    count = int(first_result["count"])

    full = request_json("esearch.fcgi", {
        "db": "pubmed",
        "retmode": "json",
        "retmax": str(count),
        "retstart": "0",
        "term": query,
    })
    result = full["esearchresult"]
    pmids = [str(x) for x in result["idlist"]]
    if len(pmids) != count or len(set(pmids)) != count:
        raise RuntimeError(f"Expected {count} unique PMIDs, received {len(pmids)} rows and {len(set(pmids))} unique")

    pmid_set = set(pmids)
    added = sorted(pmid_set - v1_set, key=int, reverse=True)
    lost = sorted(v1_set - pmid_set, key=int, reverse=True)
    overlap = v1_set & pmid_set

    sentinel_rows = []
    missing_sentinels = []
    for row in sentinels:
        retrieved = row["pmid"] in pmid_set
        if not retrieved:
            missing_sentinels.append(row)
        sentinel_rows.append([
            row["seed_id"], row["pmid"], row["title"], row["doi"],
            row["document_type"], "yes" if retrieved else "no",
        ])

    randomizer = random.Random(20260802)
    sample_pmids = randomizer.sample(pmids, min(100, len(pmids)))
    sample_records = esummary(sample_pmids)
    sample_rows = []
    for pmid in sample_pmids:
        record = sample_records.get(pmid, {})
        authors = "; ".join(author.get("name", "") for author in record.get("authors", []))
        sample_rows.append([
            pmid,
            record.get("title", ""),
            record.get("fulljournalname", ""),
            record.get("pubdate", ""),
            authors,
            "unreviewed",
            "",
            f"https://pubmed.ncbi.nlm.nih.gov/{pmid}/",
        ])

    generated = datetime.now(timezone.utc).isoformat()
    order_hash = hashlib.sha256("\n".join(pmids).encode("utf-8")).hexdigest()
    validation = {
        "generated_at_utc": generated,
        "database": "PubMed/MEDLINE",
        "platform": "NCBI E-utilities",
        "candidate_strategy_file": str(SEARCH_FILE.relative_to(ROOT)),
        "submitted_query": query,
        "query_translation": result.get("querytranslation", first_result.get("querytranslation", "")),
        "translation_stack": result.get("translationstack", first_result.get("translationstack", [])),
        "count": count,
        "unique_pmids": len(pmid_set),
        "pmid_order_sha256": order_hash,
        "comparison_with_v1": {
            "v1_count": len(v1_set),
            "v2_count": len(pmid_set),
            "overlap": len(overlap),
            "added_by_v2": len(added),
            "present_in_v1_not_v2": len(lost),
        },
        "sentinel_validation": {
            "pubmed_applicable_sentinels": len(sentinels),
            "retrieved": len(sentinels) - len(missing_sentinels),
            "missing": len(missing_sentinels),
            "recall": (len(sentinels) - len(missing_sentinels)) / len(sentinels) if sentinels else None,
            "missing_records": missing_sentinels,
        },
        "interpretation": {
            "eligibility_decisions_made": 0,
            "prisma_counts_changed": False,
            "press_status": "internal validation only; external independent PRESS still required",
            "precision_sample_size": len(sample_pmids),
        },
    }

    (OUT / "pubmed_v2_validation.json").write_text(
        json.dumps(validation, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    (OUT / "pubmed_v2_query.txt").write_text(query + "\n", encoding="utf-8")
    write_csv(
        OUT / "pubmed_v2_pmids.csv",
        ["rank", "pmid", "pubmed_url"],
        [[idx, pmid, f"https://pubmed.ncbi.nlm.nih.gov/{pmid}/"] for idx, pmid in enumerate(pmids, 1)],
    )
    write_csv(
        OUT / "pubmed_v2_sentinel_validation.csv",
        ["seed_id", "pmid", "title", "doi", "document_type", "retrieved_by_v2"],
        sentinel_rows,
    )
    write_csv(
        OUT / "pubmed_v2_comparison.csv",
        ["pmid", "in_v1", "in_v2", "classification"],
        [
            [pmid, "yes" if pmid in v1_set else "no", "yes" if pmid in pmid_set else "no",
             "overlap" if pmid in overlap else "v2_only" if pmid in pmid_set else "v1_only"]
            for pmid in sorted(v1_set | pmid_set, key=int, reverse=True)
        ],
    )
    write_csv(
        OUT / "pubmed_v2_precision_sample.csv",
        ["pmid", "title", "journal", "publication_date", "authors", "human_relevance_decision", "exclusion_reason", "pubmed_url"],
        sample_rows,
    )

    print(json.dumps({
        "count": count,
        "overlap": len(overlap),
        "added": len(added),
        "lost": len(lost),
        "sentinels": len(sentinels),
        "sentinels_missing": len(missing_sentinels),
        "pmid_order_sha256": order_hash,
    }, indent=2))


if __name__ == "__main__":
    main()
