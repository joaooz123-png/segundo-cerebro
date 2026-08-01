# Sistema de Recuperação Inteligente

## Objetivo

Recuperar contexto completo antes de qualquer produção derivada, evitando perda de fatos, correções e decisões anteriores.

## Arquitetura em duas IAs

### IA 1 — Recuperadora

Responsável por:

- decompor a solicitação em entidades, datas, produtos, instituições e eventos;
- pesquisar GitHub, Google Drive, Wisebase e fontes conectadas;
- recuperar fatos, documentos, correções e versões anteriores;
- classificar confiança e lacunas;
- montar um `Context Pack` estruturado.

A IA Recuperadora não redige a peça final.

### IA 2 — Redatora/Analista

Recebe somente o `Context Pack`, o Guia Mestre e a instrução atual.

Responsável por:

- produzir memorando, BO, petição, relatório, resumo ou plano;
- preservar terminologia e correções do usuário;
- não eliminar fatos sem justificativa explícita;
- registrar no changelog o que foi usado, omitido e acrescentado.

## Pipeline

1. `INTENT_RESOLUTION` — identificar objetivo real e pragmática da instrução.
2. `ENTITY_EXPANSION` — expandir nomes, aliases, produtos e instituições relacionadas.
3. `HYBRID_RETRIEVAL` — busca lexical + semântica + temporal + por grafo.
4. `SOURCE_RANKING` — priorizar documento original, decisão, comunicação e relato.
5. `CONFLICT_DETECTION` — detectar divergências entre versões.
6. `CORRECTION_INJECTION` — aplicar correções permanentes do usuário.
7. `CONTEXT_PACK` — gerar pacote de contexto versionado.
8. `DRAFTING` — produzir saída derivada.
9. `VALIDATION` — checar cobertura, continuidade e rastreabilidade.
10. `COMMIT` — registrar novos fatos, decisões e correções.

## Fontes e funções

- GitHub: estrutura, índices, schemas, changelog e código.
- Google Drive: arquivos originais, anexos, áudios, imagens e PDFs.
- Wisebase: recuperação semântica e síntese rápida.
- ChatGPT/File Library: recuperação de arquivos e conversas anteriores.

## Context Pack mínimo

```yaml
request_id: REQ-YYYYMMDD-NNN
query: texto original
resolved_intent: objetivo interpretado
entities: []
cases: []
facts: []
documents: []
corrections: []
prior_outputs: []
conflicts: []
gaps: []
coverage_score: 0.0
base_version: string
```

## Critério de parada

A recuperação só termina quando:

- todos os casos mencionados foram consultados;
- correções permanentes foram aplicadas;
- versões anteriores relevantes foram recuperadas;
- lacunas foram explicitadas;
- a cobertura mínima definida para o tipo de tarefa foi atingida.

Para peças jurídicas extensas, cobertura mínima recomendada: 0,90.
