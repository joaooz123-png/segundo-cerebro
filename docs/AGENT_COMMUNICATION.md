# Comunicação entre Node.js, serviços Python e agentes de coding

## Barramento central

O `apps/gateway` é o plano de controle em Node.js. Ele recebe tarefas, valida contratos, registra aprovações e encaminha trabalho para agentes especializados.

## Protocolos

1. **HTTP/JSON** para comunicação simples entre Node.js, FastAPI e workers locais.
2. **MCP** para expor ferramentas e recursos a modelos e agentes externos.
3. **GitHub branch/commit/PR** como protocolo durável para agentes de coding.
4. **Fila de tarefas** para ingestões longas, embeddings, auditorias e reconstruções.
5. **Webhooks** somente para eventos que não exijam segredo no cliente.

## Contrato mínimo de tarefa

```json
{
  "taskId": "TASK-2026-0001",
  "agent": "coding",
  "action": "implementar busca híbrida",
  "contextPackId": "CTX-2026-0042",
  "repository": "joaooz123-png/segundo-cerebro",
  "branch": "agent/hybrid-search",
  "payload": {},
  "approvalRequired": true
}
```

## Agentes

- `planner`: decompõe a tarefa e seleciona fontes.
- `retriever`: recupera fatos, correções e evidências; não redige.
- `verifier`: mede cobertura, conflitos e omissões.
- `composer`: produz a saída usando apenas o Context Pack aprovado.
- `archivist`: registra fatos, versões, relações e changelog.
- `coding`: atua em branch isolada, executa testes e abre PR.

## Regras para agentes de coding

- Nunca trabalhar diretamente na branch principal.
- Um agente por branch e por escopo.
- Toda alteração deve gerar diff auditável.
- O Context Pack deve acompanhar a tarefa.
- Nenhum segredo ou evidência sensível entra em prompt, log ou commit.
- Mudanças destrutivas e deploys exigem aprovação explícita.
- O agente deve retornar: resumo, arquivos alterados, testes, riscos e próximo ciclo.

## Integração com outros agentes

Qualquer agente compatível pode entrar por um adaptador que implemente:

- `submitTask(task)`
- `getStatus(taskId)`
- `cancelTask(taskId)`
- `getArtifacts(taskId)`
- `requestApproval(taskId, action)`

O adaptador transforma o formato do provedor no contrato interno, sem alterar a Base Mestra.
