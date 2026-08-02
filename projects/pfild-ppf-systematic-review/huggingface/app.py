from __future__ import annotations

import re
import unicodedata
from functools import lru_cache

import gradio as gr
import numpy as np
from rapidfuzz.fuzz import ratio

PF_TERMS = (
    "progressive fibrosing interstitial lung disease",
    "progressive-fibrosing interstitial lung disease",
    "progressive fibrotic interstitial lung disease",
    "progressive fibrosing ild",
    "progressive fibrotic ild",
    "progressive fibrotic phenotype",
    "progressive fibrosis phenotype",
    "pf-ild",
    "pfild",
    "progressive pulmonary fibrosis",
)


def normalize(value: str | None) -> str:
    text = unicodedata.normalize("NFKD", value or "")
    text = "".join(c for c in text if not unicodedata.combining(c))
    return re.sub(r"[^a-z0-9]+", " ", text.lower()).strip()


def identifier(value: str | None) -> str:
    text = (value or "").lower().strip()
    text = re.sub(r"^https?://(?:dx\.)?doi\.org/", "", text)
    return re.sub(r"^(doi|pmid)\s*:?\s*", "", text).strip()


@lru_cache(maxsize=1)
def embedding_model():
    from sentence_transformers import SentenceTransformer

    return SentenceTransformer("sentence-transformers/all-MiniLM-L6-v2")


@lru_cache(maxsize=1)
def screening_model():
    from transformers import pipeline

    return pipeline(
        "zero-shot-classification",
        model="MoritzLaurer/deberta-v3-base-zeroshot-v1.1-all-33",
    )


def deduplicate(title_a, title_b, doi_a, doi_b, pmid_a, pmid_b):
    if identifier(doi_a) and identifier(doi_a) == identifier(doi_b):
        return {"recommendation": "probable bibliographic duplicate", "score": 1.0, "evidence": ["exact DOI"]}
    if identifier(pmid_a) and identifier(pmid_a) == identifier(pmid_b):
        return {"recommendation": "probable bibliographic duplicate", "score": 1.0, "evidence": ["exact PMID"]}

    fuzzy = ratio(normalize(title_a), normalize(title_b)) / 100
    semantic = 0.0
    notes = []
    try:
        vectors = embedding_model().encode([title_a, title_b], normalize_embeddings=True)
        semantic = float(np.dot(vectors[0], vectors[1]))
    except Exception as exc:
        notes.append(f"semantic model unavailable: {exc}")

    score = round(0.55 * fuzzy + 0.45 * semantic, 4)
    recommendation = (
        "probable bibliographic duplicate"
        if score >= 0.93
        else "manual duplicate review"
        if score >= 0.78
        else "probably distinct reports"
    )
    notes.extend(
        [
            f"fuzzy title={fuzzy:.3f}",
            f"semantic title={semantic:.3f}",
            "Publication-family linkage must be assessed separately.",
        ]
    )
    return {"recommendation": recommendation, "score": score, "evidence": notes}


def screen(title, abstract):
    text = f"{title or ''}\n{abstract or ''}".strip()
    normalized = normalize(text)
    hits = [term for term in PF_TERMS if normalize(term) in normalized]
    ild_context = any(term in normalized for term in ("interstitial lung disease", "fibrosing ild", "fibrotic ild"))
    ipf_only = "idiopathic pulmonary fibrosis" in normalized and not any(
        term in normalized
        for term in ("non ipf", "other than idiopathic", "connective tissue", "hypersensitivity", "unclassifiable")
    )
    rule_score = 0.65 * bool(hits) + 0.20 * ild_context - 0.35 * ipf_only
    reasons = (["explicit terminology: " + ", ".join(hits[:5])] if hits else [])

    labels = [
        "directly about PF-ILD or PPF in non-IPF interstitial lung disease",
        "contextual or uncertain mention of PF-ILD or PPF",
        "not about PF-ILD or PPF",
    ]
    try:
        result = screening_model()(text[:5000], labels, multi_label=False)
        model_label = result["labels"][0]
        model_score = float(result["scores"][0])
        reasons.append(f"zero-shot: {model_label} ({model_score:.3f})")
    except Exception as exc:
        model_label, model_score = "model unavailable", 0.0
        reasons.append(f"zero-shot unavailable: {exc}")

    if ipf_only:
        recommendation = "uncertain — verify separable non-IPF data"
    elif rule_score >= 0.65 or model_label.startswith("directly"):
        recommendation = "include for human title/abstract review"
    elif rule_score > 0 or model_label.startswith("contextual"):
        recommendation = "uncertain — human review required"
    else:
        recommendation = "possible exclusion — human confirmation required"

    return {
        "recommendation": recommendation,
        "rule_score": round(rule_score, 3),
        "model_label": model_label,
        "model_score": round(model_score, 3),
        "reasons": reasons,
        "governance": "AI output is never the final eligibility decision.",
    }


def author_name(author: str) -> str:
    parts = author.strip().split()
    if len(parts) < 2:
        return author.strip()
    return f"{parts[-1]} {''.join(part[0].upper() for part in parts[:-1])}"


def vancouver(authors, title, journal, year, volume, issue, pages, doi):
    all_authors = [item.strip() for item in re.split(r"[;\n]+", authors or "") if item.strip()]
    rendered = ", ".join(author_name(item) for item in all_authors[:6])
    rendered += ", et al." if len(all_authors) > 6 else "."
    citation = f"{rendered} {title.strip()}. {journal.strip()}. {str(year).strip()}"
    if volume:
        citation += f";{volume}" + (f"({issue})" if issue else "")
    if pages:
        citation += f":{pages}"
    citation += "."
    if identifier(doi):
        citation += f" doi:{identifier(doi)}."
    return {
        "citation": re.sub(r"\s+", " ", citation).strip(),
        "all_authors_preserved": all_authors,
        "warning": "Verify the MEDLINE journal abbreviation and pagination before manuscript use.",
    }


with gr.Blocks(title="PF-ILD Review Agents") as demo:
    gr.Markdown("# PF-ILD / PPF Review Agents\nPrivate decision support. **Human confirmation is mandatory.**")

    with gr.Tab("Deduplicator"):
        with gr.Row():
            ta, tb = gr.Textbox(label="Title A"), gr.Textbox(label="Title B")
        with gr.Row():
            da, db = gr.Textbox(label="DOI A"), gr.Textbox(label="DOI B")
        with gr.Row():
            pa, pb = gr.Textbox(label="PMID A"), gr.Textbox(label="PMID B")
        button = gr.Button("Compare", variant="primary")
        output = gr.JSON()
        button.click(deduplicate, [ta, tb, da, db, pa, pb], output)

    with gr.Tab("High-recall screener"):
        screening_title = gr.Textbox(label="Title")
        screening_abstract = gr.Textbox(label="Abstract", lines=10)
        button = gr.Button("Recommend", variant="primary")
        output = gr.JSON()
        button.click(screen, [screening_title, screening_abstract], output)

    with gr.Tab("Vancouver formatter"):
        authors = gr.Textbox(label="All authors", lines=8)
        title = gr.Textbox(label="Title")
        journal = gr.Textbox(label="MEDLINE journal abbreviation")
        with gr.Row():
            year, volume, issue, pages = [gr.Textbox(label=label) for label in ("Year", "Volume", "Issue", "Pages/article")]
        doi = gr.Textbox(label="DOI")
        button = gr.Button("Format", variant="primary")
        output = gr.JSON()
        button.click(vancouver, [authors, title, journal, year, volume, issue, pages, doi], output)

if __name__ == "__main__":
    demo.launch()
