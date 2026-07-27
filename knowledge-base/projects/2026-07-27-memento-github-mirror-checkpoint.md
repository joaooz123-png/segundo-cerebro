# Checkpoint — Espelhamento do MEMENTO no GitHub

**Data:** 27/07/2026  
**Estado:** vault canônico funcionando; espelho aguardando autenticação e liberação do destino  
**Origem canônica:** `joaooz123-png/segundo-cerebro`  
**Destino planejado:** `JoaoRG-lab/memento-vault`

## Diagnóstico

### Funcionando

- O MEMENTO canônico está em https://github.com/joaooz123-png/segundo-cerebro.
- Branch padrão confirmada: `mainn`.
- Marcadores do vault confirmados:
  - `knowledge-base/`;
  - `data-feeds/`;
  - `workflows/`;
  - `.github/workflows/`.
- A skill `ciclo-memento` foi criada e conectada ao vault.
- O arquivo `AGENTS.md` foi adicionado no commit `fed2b9e4fbd1dcc5d27d72ae86b4f796f0680566`.
- O `AGENTS.md` obriga o Ciclo MEMENTO e bloqueia auditorias amplas, repetidas ou dependentes de pré-condições ausentes.
- Um snapshot integral foi preparado no commit `fed2b9e`, com 195 arquivos rastreados naquele momento.
- O commit mais recente observado no início deste checkpoint foi `c8cc529cdabfb366e3e48ab8539d3fc8b89c0348`.
- As instalações GitHub das duas contas foram identificadas:
  - `joaooz123-png`: instalação `106540915`;
  - `JoaoRG-lab`: instalação `133240770`.

### Incompleto

- O espelho desejado é unidirecional:
  - origem: `joaooz123-png/segundo-cerebro`;
  - destino: `JoaoRG-lab/memento-vault`.
- `JoaoRG-lab/memento-vault` ainda retorna `404` para a integração e não aparece entre os repositórios instalados.
- Não foi possível confirmar se o destino está privado e fora da seleção da instalação ou se a criação não foi concluída.
- O espelhamento ainda não foi gravado nem validado.
- A política final das GitHub Actions do espelho ainda precisa ser confirmada para impedir execuções duplicadas.

### Bloqueio confirmado

- A instalação `133240770` do `JoaoRG-lab` expõe escrita apenas em `JoaoRG-lab/rhema-care-flow`.
- `JoaoRG-lab/site-casamento` é visível publicamente, mas aparece somente para leitura e não pertence a este trabalho.
- `rhema-care-flow` está explicitamente fora do escopo e não foi alterado.
- O Cloud Browser abriu https://github.com/settings/installations/133240770, mas encontrou a tela de login do GitHub.
- Nenhuma senha, token, código de autenticação ou credencial foi capturada ou armazenada.
- GitHub CLI e token local não estão disponíveis; a integração não expõe criação de repositório nem alteração da seleção da instalação.

## Propostas priorizadas

1. **Autenticar manualmente no GitHub pelo Cloud Browser** — impacto alto, esforço baixo.
2. **Adicionar somente `memento-vault` à instalação `133240770`** — impacto alto, esforço baixo após login.
3. **Validar escrita no destino e sua branch padrão** — impacto alto, esforço baixo.
4. **Espelhar o vault preservando a origem como canônica** — impacto alto, esforço médio.
5. **Impedir Actions duplicadas no destino** — impacto alto, esforço baixo após o espelho.

## Ação realizada neste ciclo

- Consolidado este checkpoint técnico no vault canônico.
- Registrados fatos confirmados, bloqueios, decisões e o ponto exato de retomada.
- Auditoria ampla dispensada como **não aplicável**, pois a alteração é somente documental.
- Nenhum workflow remoto foi disparado.
- Nenhum repositório do `JoaoRG-lab` foi modificado.

## Ponto exato de retomada

1. Abrir esta conversa em https://chatgpt.com.
2. Abrir o painel Cloud Browser já posicionado no login do GitHub.
3. Autenticar diretamente no GitHub sem enviar credenciais pelo chat.
4. Responder **“logado”**.
5. Na instalação `133240770`, selecionar somente `memento-vault` e salvar.
6. Confirmar via integração que o destino ficou acessível com `push: true`.
7. Espelhar `joaooz123-png/segundo-cerebro` para `JoaoRG-lab/memento-vault`.
8. Validar branch, commit, arquivos essenciais e ausência de execução duplicada das Actions.

## Resumo para log

Vault canônico e skill Ciclo MEMENTO confirmados e conectados.
Espelho definido de joaooz123-png/segundo-cerebro para JoaoRG-lab/memento-vault.
Bloqueio atual é autenticação/seleção do destino na instalação GitHub 133240770.
Nenhuma credencial, auditoria ampla ou alteração no rhema-care-flow foi realizada.
próximo ciclo sugerido: autenticar no GitHub, liberar o destino e executar o espelhamento