# Checkpoint — Site do casamento João & Taís

**Data:** 27/07/2026  
**Estado:** protótipo funcional, publicado e em evolução  
**Regra permanente:** depois de cada mudança solicitada no site, executar novo deploy. O projeto continua sendo um protótipo; não transformar dados pendentes em informações finais inventadas.

## Diagnóstico

### Funcionando

- Site público: https://joao-e-tais-casamento.vercel.app
- Repositório canônico público: https://github.com/JoaoRG-lab/joao-e-tais-casamento
  - Branch de produção: `main`
  - Commit publicado e verificado: `4751790d2464f014fee31506c0497e8854792b00`
  - Mensagem: `feat: publish complete wedding site prototype`
  - Conteúdo real publicado: React + TypeScript + Vite, API RSVP, esquema Supabase, configurações, testes e lockfile.
  - Arquivos locais sensíveis ou gerados não foram publicados: `.env`, `node_modules`, `dist`, banco bruto de Cartas a Taís e imagens temporárias.
- Projeto Vercel existente: `joao-e-tais-casamento`
  - Project ID: `prj_LAGyUDfJ07NsYclBuM21XxHQHUOD`
  - Team ID: `team_w17xyaWTNSYgGTyw6LAVVHC2`
  - Repositório conectado: `JoaoRG-lab/joao-e-tais-casamento`
  - Branch `main` reconhecida como produção.
  - Deployment Git atual: `dpl_E5rmt7VnhWFosELxXG7NExgczXF8`
  - Estado confirmado: `READY`, produção, sem erro de alias.
  - URL específica: https://joao-e-tais-casamento-d24crxc2o-joaorg-labs-projects.vercel.app
  - Alias principal atualizado: https://joao-e-tais-casamento.vercel.app
- Build remoto confirmado:
  - clone do GitHub no commit `4751790`;
  - `tsc -b && vite build` aprovado;
  - 1.589 módulos transformados;
  - build concluído em aproximadamente 11 segundos.
- Verificação publicada:
  - página principal respondeu HTTP 200;
  - HTML, CSS, JavaScript e fontes publicados;
  - conteúdo acessível renderizado com navegação, história, cerimônia, RSVP, presentes e informações;
  - navegação “Nossa história” levou a `#historia`;
  - validação do formulário vazio exibiu “Informe seu nome completo.”;
  - rota `/api/rsvp` respondeu 405 para GET e declarou `Allow: POST`;
  - nenhum erro de runtime encontrado no período verificado.
- RSVP real preservado: na ausência de Supabase dedicado, a API server-side usa o endpoint de contingência D1 publicado. Nenhum RSVP fictício foi gravado durante os testes.
- Identidade visual preservada:
  - EB Garamond + Manrope;
  - marfim, verde-floresta, vinho e dourado;
  - molduras vitorianas e ornamentos botânicos;
  - medalha de São Bento, Aldebaran e Plêiades;
  - narrativa editorial inspirada em Cartas a Taís.
- “Nossa história” permanece estruturada em quatro capítulos: Presença; Cartas; Entre a névoa e as estrelas; O nosso sim.
- Proteção de protótipo: `noindex, nofollow, noarchive` e cabeçalho `X-Robots-Tag`.

### Incompleto

- Dados finais deliberadamente pendentes: data, horário, endereços, traje, prazo de RSVP, lista de presentes e fotos.
- O projeto Vercel não possui variáveis de ambiente de projeto.
- Supabase dedicado ao casamento ainda não existe. Os projetos conectados atuais são `Rhema-care-flow` e `telemedicina-agendamento`; não reutilizar nenhum deles.
- Slack ainda não está ligado ao RSVP porque não existe `SLACK_WEBHOOK_URL` configurada.
- MyRegistry, domínio próprio, Cloudflare e Metabase permanecem para ciclos futuros.
- A linhagem Git local é anterior e diferente da primeira publicação remota; não executar reset destrutivo para “sincronizar” históricos.

### Bloqueios confirmados

- Criar um projeto Supabase dedicado envolve custo e exige que o usuário escolha explicitamente a organização antes da confirmação de cobrança.
- Configurar Slack no backend exige uma credencial/webhook apropriada; não inventar, copiar ou expor segredo.
- O envio completo de RSVP até persistência não foi testado com dados fictícios, por decisão de segurança e integridade dos dados.

## Propostas priorizadas

1. **Criar Supabase dedicado ao casamento** — impacto alto, esforço médio. Após escolha explícita da organização e confirmação do custo, aplicar `supabase/schema.sql`, verificar RLS e conectar as variáveis server-side na Vercel.
2. **Ligar notificações reais do Slack** — impacto médio, esforço baixo após disponibilizar webhook seguro; validar sem expor o segredo.
3. **Definir data, locais e traje** — impacto máximo para o convidado, esforço baixo assim que as informações forem confirmadas.
4. **Integrar lista MyRegistry e domínio próprio** — impacto médio, esforço médio; executar apenas quando links/domínio forem escolhidos.
5. **Alinhar o histórico Git local ao remoto sem perder trabalho** — impacto operacional médio, esforço médio; fazer por merge/rebase controlado, nunca por reset destrutivo.

## Ação

- Publicado o repositório canônico completo no GitHub.
- Conectado o projeto Vercel existente ao repositório público e à branch `main`.
- Criado e verificado o deployment de produção do commit `4751790`.
- Validada a página pública, navegação, validação inicial do RSVP, rota server-side e ausência de erros de runtime.
- Atualizado este checkpoint operacional no MEMENTO canônico.
- Auditoria ampla dispensada como **não aplicável** para o MEMENTO, pois esta alteração é apenas documental.
- Nenhuma credencial, resposta de convidado, dado clínico ou conteúdo bruto de Cartas a Taís foi registrado.

## Resumo para log

GitHub canônico criado e preenchido com o código real do protótipo no commit `4751790`.
Projeto Vercel existente conectado ao GitHub e deployment `dpl_E5rmt7VnhWFosELxXG7NExgczXF8` confirmado como `READY`.
Site público respondeu HTTP 200, renderizou conteúdo e navegação, e não apresentou erros de runtime no período verificado.
Supabase e Slack continuam pendentes por custo/credencial; o RSVP real via D1 permanece ativo e nenhum dado fictício foi gravado.
próximo ciclo sugerido: escolher a organização para criar o Supabase dedicado ao casamento
