# RG Knowledge OS — Arquitetura

## Decisão
O sistema terá backend e frontend, mas em fases.

## MVP
1. Backend de ingestão, normalização, indexação e recuperação.
2. Interface mínima para busca, revisão de Context Packs e correções.
3. Sem conteúdo sensível enquanto o repositório permanecer público.

## Componentes

### Backend
- API de ingestão
- pipeline ETL documental
- extrator de entidades
- normalizador de fatos
- busca híbrida lexical + semântica + temporal
- grafo de relações
- detector de conflitos
- gerador de Context Packs
- trilha de auditoria

### Frontend
- caixa de busca
- filtros por caso, instituição, data, status e força probatória
- timeline
- visualização de fatos e documentos relacionados
- tela de conflitos
- editor de correções permanentes
- aprovação humana antes de consolidar fatos

## Princípio
A IA recuperadora nunca redige a peça final. Ela entrega um Context Pack versionado para a IA analista/redatora.

## Fases
- Fase 1: backend local e CLI
- Fase 2: API e painel web mínimo
- Fase 3: sincronização com Drive, Wisebase e GitHub
- Fase 4: grafo, agentes especializados e testes de continuidade
