from __future__ import annotations

import collect_sentinel_citations as collector


def corrected_items(payload):
    for section, item in (("referenceList", "reference"), ("citationList", "citation")):
        if section not in payload:
            continue
        value = payload.get(section, {}).get(item, [])
        if isinstance(value, dict):
            return [value]
        if isinstance(value, list):
            return value
    value = payload.get("resultList", {}).get("result", [])
    return [value] if isinstance(value, dict) else value


collector.items = corrected_items
collector.main()
