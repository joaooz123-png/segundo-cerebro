# Retriever

Agente interno responsável por recuperar contexto antes da redação.

Pipeline obrigatório:

1. decompor a solicitação;
2. identificar entidades, casos e correções permanentes;
3. buscar por texto, vetor, tempo e relações;
4. detectar conflitos e lacunas;
5. calcular cobertura;
6. produzir um Context Pack versionado;
7. bloquear a redação quando a cobertura mínima não for atingida.

A IA recuperadora não redige peças finais.
