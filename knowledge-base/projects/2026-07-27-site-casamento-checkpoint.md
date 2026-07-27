# Checkpoint — Site do casamento João & Taís

**Data:** 27/07/2026  
**Estado:** protótipo funcional, publicado e em evolução  
**Regra permanente:** depois de cada mudança solicitada no site, executar novo deploy. O projeto continua sendo um protótipo; não transformar dados pendentes em informações finais inventadas.

## Diagnóstico

### Funcionando

- Site público: https://joao-e-tais-casamento.vercel.app
- Projeto Vercel existente: `joao-e-tais-casamento`
  - Project ID: `prj_LAGyUDfJ07NsYclBuM21XxHQHUOD`
  - Team ID: `team_w17xyaWTNSYgGTyw6LAVVHC2`
  - Último deployment confirmado: `dpl_25rwfJdpnMQPmNYNujzTpisefsZt`
  - Estado confirmado: `READY`, produção, sem erro de alias.
- Código local em React + TypeScript + Vite, branch `main`.
- Commit local mais recente: `158b3e7 feat: expand wedding story into an editorial journey`.
- Histórico local relevante:
  - `48d4708` — linguagem visual de Cartas a Taís;
  - `7662725` — RSVP da Vercel encaminhado ao backend D1 publicado;
  - `2f9de3c` — artefatos TypeScript ignorados;
  - `721745c` — criação inicial.
- Validações executadas:
  - 3 testes Vitest aprovados;
  - build TypeScript/Vite aprovado;
  - nenhum arquivo `.env` real rastreado;
  - varredura sem padrões de credenciais.
- RSVP funcional: rota server-side da Vercel encaminha para o endpoint Cloudflare D1 já publicado quando não existe Supabase dedicado.
- `supabase/schema.sql` está preparado para migração futura com RLS e escrita somente server-side.
- Identidade visual atual:
  - EB Garamond + Manrope;
  - marfim, verde-floresta, vinho e dourado;
  - molduras vitorianas e ornamentos botânicos;
  - medalha de São Bento, Aldebaran e Plêiades;
  - narrativa editorial inspirada em Cartas a Taís.
- “Nossa história” estruturada em quatro capítulos:
  1. Presença;
  2. Cartas;
  3. Entre a névoa e as estrelas;
  4. O nosso sim.
- Proteção de protótipo: `noindex, nofollow, noarchive` e cabeçalho `X-Robots-Tag`.

### Incompleto

- Dados finais ainda deliberadamente pendentes: data, horário, endereços, traje, prazo de RSVP, lista de presentes e fotos.
- Supabase dedicado, Slack, MyRegistry, domínio e Metabase ainda não foram concluídos.
- O código local ainda não está sincronizado com um repositório GitHub gravável.
- O projeto Vercel ainda não está conectado a um repositório GitHub canônico.

### Bloqueio confirmado

- Repositório público existente: https://github.com/JoaoRG-lab/site-casamento
- Ele está vazio e usa `main`, mas a integração retorna `push: false`.
- Teste real de criação de `README.md` recusado pelo GitHub:
  - `403 — Resource not accessible by integration`.
- A instalação GitHub `133240770` expõe escrita apenas em `JoaoRG-lab/rhema-care-flow`; não alterar esse projeto.
- A permissão interna do plugin GitHub no ChatGPT foi atualizada para `full_access`, mas isso não substitui autenticação nem seleção do repositório no GitHub.
- GitHub CLI `gh` não está instalado no ambiente local.
- Cloud Browser aberto na tela de login do GitHub; nenhuma senha, token ou código foi capturado.

## Propostas priorizadas

1. **Retomar a autenticação no Cloud Browser** — impacto alto, esforço baixo. Destrava criação/configuração do GitHub sem compartilhar credenciais no chat.
2. **Criar o repositório canônico `JoaoRG-lab/joao-e-tais-casamento`** — impacto alto, esforço baixo após login. Não excluir nem sobrescrever `site-casamento`.
3. **Publicar o snapshot validado na `main`** — impacto alto, esforço médio. Excluir `.env`, banco bruto das cartas, `dist`, `node_modules` e arquivos temporários.
4. **Conectar o repositório ao projeto Vercel existente** — impacto alto, esforço médio. Não criar segundo projeto Vercel; preservar IDs, domínios e variáveis.
5. **Validar o fluxo completo GitHub → Vercel → RSVP** — impacto alto, esforço baixo após integração.

## Ação realizada neste ciclo

- Criado este checkpoint operacional no MEMENTO canônico.
- Preparado o mesmo conteúdo para persistência no AI Wisebase.
- Auditoria ampla dispensada como **não aplicável**, pois a alteração é apenas documental.
- Nenhuma credencial, dado clínico ou conteúdo bruto de Cartas a Taís foi incluído.
- Nenhuma modificação foi feita no site, na Vercel ou no `rhema-care-flow`.

## Ponto exato de retomada

1. Abrir esta conversa no https://chatgpt.com, preferencialmente em computador.
2. Abrir o painel **Cloud Browser — GitHub — site do casamento**.
3. Assumir o controle e autenticar diretamente no GitHub; nunca enviar senha ou código pelo chat.
4. Responder **“logado”**.
5. Criar `JoaoRG-lab/joao-e-tais-casamento`, público, com `main`.
6. Liberar esse repositório para a integração GitHub.
7. Publicar o código validado.
8. Conectar ao projeto Vercel existente e confirmar `main` como produção.
9. Verificar repositório, deployment e RSVP real.

## Resumo para log

Checkpoint do site do casamento salvo com estado técnico, identidade visual, testes e integrações.
Site permanece publicado na Vercel e o RSVP real via D1 continua preservado.
Bloqueio atual é a autenticação/seleção do repositório no GitHub; nenhuma credencial foi armazenada.
Retomada deve começar pelo Cloud Browser já aberto na tela de login.
próximo ciclo sugerido: autenticar no GitHub e publicar o código no repositório canônico
