from __future__ import annotations

from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable
import json
import re

STATUS_PRIORITY = {
    "DOCUMENTADO": 5,
    "CONTESTADO": 4,
    "RELATADO": 3,
    "INFERIDO": 2,
    "PENDENTE": 1,
}

@dataclass(slots=True)
class Fact:
    id: str
    title: str
    status: str
    summary: str
    entities: list[str] = field(default_factory=list)
    sources: list[str] = field(default_factory=list)
    corrections: list[str] = field(default_factory=list)
    updated_at: str = ""

@dataclass(slots=True)
class ContextPack:
    request_id: str
    query: str
    resolved_intent: str
    entities: list[str]
    facts: list[Fact]
    corrections: list[str]
    gaps: list[str]
    coverage_score: float
    generated_at: str

    def to_json(self) -> str:
        return json.dumps(asdict(self), ensure_ascii=False, indent=2)


def normalize(text: str) -> set[str]:
    return set(re.findall(r"[a-zA-ZÀ-ÿ0-9_-]+", text.lower()))


def lexical_score(query: str, fact: Fact) -> float:
    q = normalize(query)
    haystack = normalize(" ".join([fact.title, fact.summary, *fact.entities]))
    if not q:
        return 0.0
    return len(q & haystack) / len(q)


def rank_facts(query: str, facts: Iterable[Fact]) -> list[Fact]:
    ranked = sorted(
        facts,
        key=lambda f: (
            lexical_score(query, f),
            STATUS_PRIORITY.get(f.status, 0),
            f.updated_at,
        ),
        reverse=True,
    )
    return [f for f in ranked if lexical_score(query, f) > 0]


def build_context_pack(
    query: str,
    resolved_intent: str,
    entities: list[str],
    facts: list[Fact],
    corrections: list[str],
    gaps: list[str],
) -> ContextPack:
    selected = rank_facts(query + " " + " ".join(entities), facts)
    documented = sum(1 for f in selected if f.status == "DOCUMENTADO")
    coverage = min(1.0, (len(selected) + documented) / max(1, len(entities) * 2))
    now = datetime.now(timezone.utc)
    return ContextPack(
        request_id=f"REQ-{now:%Y%m%d%H%M%S}",
        query=query,
        resolved_intent=resolved_intent,
        entities=entities,
        facts=selected,
        corrections=corrections,
        gaps=gaps,
        coverage_score=round(coverage, 2),
        generated_at=now.isoformat(),
    )


def load_facts(path: Path) -> list[Fact]:
    data = json.loads(path.read_text(encoding="utf-8"))
    return [Fact(**item) for item in data]


def main() -> None:
    import argparse

    parser = argparse.ArgumentParser(description="Gera Context Packs do RG Knowledge OS")
    parser.add_argument("query")
    parser.add_argument("--facts", type=Path, required=True)
    parser.add_argument("--intent", default="recuperar contexto completo")
    parser.add_argument("--entities", nargs="*", default=[])
    parser.add_argument("--output", type=Path, default=Path("context_pack.json"))
    args = parser.parse_args()

    facts = load_facts(args.facts)
    pack = build_context_pack(
        query=args.query,
        resolved_intent=args.intent,
        entities=args.entities,
        facts=facts,
        corrections=[],
        gaps=[],
    )
    args.output.write_text(pack.to_json(), encoding="utf-8")
    print(args.output)


if __name__ == "__main__":
    main()
