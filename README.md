# Segundo Cerebro - MEMENTO v1

Sistema autonomo de crescimento de conhecimento 24/7.
**Maestro:** Joao Otavio Renno Grilo

## Estrutura
```
/knowledge-base/    <- cards markdown por tema
/data-feeds/        <- dados atualizados automaticamente
/workflows/         <- scripts Python
/.github/workflows/ <- GitHub Actions 24/7
```

## Workflows ativos
| Workflow | Frequencia | Funcao |
|----------|-----------|--------|
| knowledge-growth.yml | Diario 06h BRT | Crawl RSS: HackerNews, arXiv IA, PubMed, InfoMoney |
| market-data.yml | A cada 2h (07-22h uteis) | PETR4, VALE3, ITUB4, IBOV, USD/BRL, BTC |
| wisebase-sync.yml | A cada 6h | Sync /knowledge-base/ -> Wisebase API |
