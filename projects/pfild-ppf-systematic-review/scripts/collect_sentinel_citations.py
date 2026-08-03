from __future__ import annotations

import csv, hashlib, json, time, urllib.parse, urllib.request
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "artifacts" / "citation_chasing"
RAW = OUT / "raw"
SENTINELS = ROOT / "data" / "pubmed_v2_validation" / "pubmed_v2_sentinel_validation.csv"
UNION = ROOT / "data" / "pubmed_v2_validation" / "pubmed_candidate_union_pmids.csv"
BASE = "https://www.ebi.ac.uk/europepmc/webservices/rest"
UA = "pfild_ppf_systematic_review/1.7 (+https://github.com/joaooz123-png/segundo-cerebro)"


def rows(path):
    with path.open(encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


def save_csv(path, data, fields):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8-sig", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fields, extrasaction="ignore")
        w.writeheader(); w.writerows(data)


def get_json(url):
    req = urllib.request.Request(url, headers={"User-Agent": UA, "Accept": "application/json"})
    for attempt in range(5):
        try:
            with urllib.request.urlopen(req, timeout=120) as r:
                raw = r.read()
            return json.loads(raw), raw
        except Exception:
            if attempt == 4: raise
            time.sleep(2 ** attempt)


def items(payload):
    for section, item in (("referenceList", "reference"), ("citationList", "citation")):
        value = payload.get(section, {}).get(item, [])
        if isinstance(value, dict): return [value]
        if isinstance(value, list): return value
    value = payload.get("resultList", {}).get("result", [])
    return [value] if isinstance(value, dict) else value


def val(obj, *keys):
    for key in keys:
        value = obj.get(key)
        if value not in (None, "", []):
            return str(value[0] if isinstance(value, list) else value)
    return ""


def flatten(obj):
    source = val(obj, "source", "src").upper()
    ext_id = val(obj, "id", "extId", "ext_id")
    pmid = ext_id if source == "MED" and ext_id.isdigit() else val(obj, "pmid")
    doi = val(obj, "doi").lower().strip()
    key = f"{source}:{ext_id}" if source and ext_id else (f"DOI:{doi}" if doi else "")
    return {
        "candidate_source": source, "candidate_id": ext_id, "candidate_pmid": pmid,
        "candidate_doi": doi, "candidate_title": val(obj, "title"),
        "candidate_authors": val(obj, "authorString", "authors"),
        "candidate_journal": val(obj, "journalTitle", "journalAbbreviation"),
        "candidate_year": val(obj, "pubYear", "year"), "candidate_key": key,
    }


def collect(pmid, endpoint):
    result, manifest, page = [], [], 1
    while True:
        url = f"{BASE}/MED/{pmid}/{endpoint}?page={page}&pageSize=1000&format=json"
        payload, raw = get_json(url)
        path = RAW / pmid / f"{endpoint}_{page:03d}.json"
        path.parent.mkdir(parents=True, exist_ok=True); path.write_bytes(raw)
        page_items = items(payload); result.extend(page_items)
        manifest.append({"pmid":pmid,"endpoint":endpoint,"page":page,"url":url,
                         "file":str(path.relative_to(OUT)),"sha256":hashlib.sha256(raw).hexdigest(),
                         "items":len(page_items)})
        if len(page_items) < 1000: break
        page += 1; time.sleep(.22)
    return result, manifest


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    seeds = [r for r in rows(SENTINELS) if r.get("pmid", "").strip()]
    if len(seeds) != 62: raise RuntimeError(f"expected 62 sentinels, found {len(seeds)}")
    union = {r["pmid"] for r in rows(UNION)}
    edges, manifest, failures, coverage = [], [], [], []
    for index, seed in enumerate(seeds, 1):
        pmid, counts = seed["pmid"], {}
        for endpoint in ("references", "citations"):
            try:
                found, pages = collect(pmid, endpoint); manifest += pages; counts[endpoint] = len(found)
                for obj in found:
                    candidate = flatten(obj)
                    if not candidate["candidate_key"]: continue
                    edges.append({"seed_id":seed["seed_id"],"seed_pmid":pmid,
                                  "seed_title":seed["title"],
                                  "direction":"backward" if endpoint=="references" else "forward",
                                  **candidate,
                                  "candidate_in_pubmed_union":"yes" if candidate["candidate_pmid"] in union else "no",
                                  "human_status":"not reviewed"})
            except Exception as exc:
                failures.append({"seed_id":seed["seed_id"],"seed_pmid":pmid,
                                 "endpoint":endpoint,"error":repr(exc)})
                counts[endpoint] = "failed"
            time.sleep(.22)
        coverage.append({"seed_id":seed["seed_id"],"seed_pmid":pmid,"seed_title":seed["title"],
                         "references":counts.get("references"),"citations":counts.get("citations")})
        print(f"{index}/62 {pmid} {counts}")

    unique, dirs, linked = {}, defaultdict(set), defaultdict(set)
    for edge in edges:
        key=edge["candidate_key"]
        unique.setdefault(key,{k:edge[k] for k in ("candidate_key","candidate_source","candidate_id",
            "candidate_pmid","candidate_doi","candidate_title","candidate_authors",
            "candidate_journal","candidate_year","candidate_in_pubmed_union")})
        dirs[key].add(edge["direction"]); linked[key].add(edge["seed_id"])
    unique_rows=[]
    for key,row in unique.items():
        unique_rows.append({**row,"directions":"; ".join(sorted(dirs[key])),
                            "number_of_sentinels":len(linked[key]),
                            "sentinels":"; ".join(sorted(linked[key])),"human_status":"not reviewed"})
    unique_rows.sort(key=lambda r:(r["candidate_in_pubmed_union"]=="yes",-r["number_of_sentinels"],r["candidate_key"]))

    edge_fields=list(edges[0]) if edges else []
    unique_fields=list(unique_rows[0]) if unique_rows else []
    save_csv(OUT/"sentinel_citation_edges.csv",edges,edge_fields)
    save_csv(OUT/"unique_citation_candidates.csv",unique_rows,unique_fields)
    save_csv(OUT/"sentinel_citation_coverage.csv",coverage,["seed_id","seed_pmid","seed_title","references","citations"])
    save_csv(OUT/"citation_chasing_failures.csv",failures,["seed_id","seed_pmid","endpoint","error"])
    (OUT/"raw_manifest.json").write_text(json.dumps(manifest,indent=2),encoding="utf-8")
    summary={"generated_at_utc":datetime.now(timezone.utc).isoformat(),"sentinels_processed":62,
             "endpoint_requests":len(manifest),"edge_count":len(edges),
             "unique_candidate_records":len(unique_rows),
             "unique_candidates_in_pubmed_union":sum(r["candidate_in_pubmed_union"]=="yes" for r in unique_rows),
             "unique_candidates_outside_pubmed_union":sum(r["candidate_in_pubmed_union"]=="no" for r in unique_rows),
             "direction_counts":dict(Counter(e["direction"] for e in edges)),"failures":len(failures),
             "human_eligibility_decisions_created":0,"prisma_counts_changed":0}
    (OUT/"citation_chasing_summary.json").write_text(json.dumps(summary,indent=2),encoding="utf-8")
    print(json.dumps(summary,indent=2))
    if failures: raise RuntimeError(f"{len(failures)} endpoint failures")

if __name__ == "__main__": main()
