# RG Knowledge OS API

Backend responsável por ingestão, normalização, recuperação e geração de Context Packs.

## Stack sugerida
- Python 3.12
- FastAPI
- Pydantic
- PostgreSQL + pgvector
- SQLAlchemy
- Redis opcional
- Neo4j opcional na fase de grafo

## Endpoints MVP
- `POST /ingest`
- `POST /facts`
- `GET /facts/{id}`
- `POST /retrieve`
- `POST /context-packs`
- `GET /conflicts`
- `POST /corrections`

## Regra de segurança
Nenhum documento sensível deve ser persistido neste repositório público. O backend deverá trabalhar com referências seguras ao Google Drive e metadados mínimos.
