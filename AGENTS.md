# MEMENTO Vault — instruções para o Codex

## Identidade e escopo

Este repositório é o workspace canônico `memento-vault` do MEMENTO no Codex.

- Repositório: `joaooz123-png/segundo-cerebro`
- Branch padrão: `mainn`
- Marcadores esperados: `knowledge-base/`, `data-feeds/`, `workflows/` e `.github/workflows/`
- `rhema-care-flow` não pertence ao MEMENTO e nunca deve ser usado como substituto deste vault.

Ao revisar, evoluir ou depurar este projeto, usar `$ciclo-memento` e seguir: Diagnóstico → Propostas → Ação → Resumo para log. Fazer uma melhoria prioritária por ciclo e preservar alterações não relacionadas.

## Gate obrigatório de auditoria

Não executar auditoria ampla por padrão. Antes de validar:

1. Confirmar que o remoto e os marcadores correspondem a este vault.
2. Inspecionar o diff e identificar exatamente o comportamento alterado.
3. Escolher a menor validação capaz de testar esse comportamento.
4. Verificar previamente se comando, dependências, rede, credenciais e segredos necessários estão disponíveis.

### Matriz de validação

- Apenas Markdown, cards ou índices: revisar estrutura, referências e consistência do conteúdo afetado. Auditoria de código é `não aplicável`.
- Python: usar primeiro `python -m py_compile` nos arquivos alterados e testes direcionados existentes.
- `workflows/fetch_knowledge.py` e `workflows/fetch_market.py`: não executar como teste genérico; dependem de fontes externas e rede.
- `workflows/sync_wisebase.py`: executar somente quando a mudança envolver a sincronização e `WISEBASE_API_URL` e `WISEBASE_API_KEY` estiverem disponíveis. Segredo ausente é pré-condição não atendida, não falha nova do código.
- GitHub Actions: validar sintaxe, caminhos, comandos e uso de segredos sem disparar workflow remoto apenas para descobrir se a configuração externa existe.

### Antirrepetição

- Não repetir uma auditoria que falhou pela mesma causa enquanto código, configuração, credencial, acesso ou ambiente relevante não tiverem mudado.
- Não transformar `não aplicável` ou `bloqueada por pré-condição` em falha.
- Nunca afirmar que uma auditoria foi executada ou aprovada quando ela foi dispensada.
- Executar auditoria ampla somente a pedido explícito do usuário ou quando o diff atravessar múltiplos componentes e houver um comando confiável já definido no projeto.

## Encerramento

Registrar em 3–5 linhas o que mudou, qual validação foi realmente executada e qualquer limitação. Nunca declarar o MEMENTO “pronto”. Encerrar com `próximo ciclo sugerido: X`.
