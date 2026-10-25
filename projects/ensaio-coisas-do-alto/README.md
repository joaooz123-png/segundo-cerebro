# Um Ensaio sobre as Coisas do Alto

Laboratório público para escrever, pesquisar e revisar um livro ensaístico sobre fé, sofrimento, vocação, inteligência, amor, medicina, tecnologia e reconstrução humana.

## Princípio editorial

O agente não substitui o autor. Ele atua como **pesquisador, arquiteto de argumentos, editor crítico e guardião de coerência**.

- O manuscrito público contém apenas material deliberadamente publicado.
- A memória pessoal permanece no Wisebase/MEMENTO e nunca é sincronizada integralmente.
- Toda importação do MEMENTO deve ser resumida, desidentificada e revisada pelo autor.
- Fontes externas devem ser registradas com autoria, data, URL e grau de confiança.
- O livro deve distinguir experiência pessoal, interpretação, doutrina, evidência e hipótese.

## Stack

- **Frontend e API:** Next.js + TypeScript
- **Deploy:** Vercel
- **Memória pública e busca:** Supabase/Postgres com full-text search; pgvector fica preparado para a segunda etapa
- **Modelo aberto:** Hugging Face Inference Providers, via endpoint compatível com OpenAI
- **Versionamento editorial:** GitHub, Markdown e pull requests
- **Memória privada:** AI Wisebase/MEMENTO, fora do repositório público

## Estrutura

```text
app/                  interface e API do agente
lib/                  orquestração, prompts e acesso ao Supabase
book/                 carta editorial e manuscrito público
supabase/migrations/  schema reproduzível
.github/workflows/    validação automática
```

## Executar localmente

```bash
npm install
cp .env.example .env.local
npm run dev
```

Variáveis necessárias:

```env
HF_TOKEN=
HF_MODEL=Qwen/Qwen3-4B-Instruct-2507
NEXT_PUBLIC_SUPABASE_URL=
NEXT_PUBLIC_SUPABASE_PUBLISHABLE_KEY=
```

O token do Hugging Face é usado somente na rota server-side. Nunca o exponha com prefixo `NEXT_PUBLIC_`.

## Modos do agente

- **Arquitetar:** transforma uma ideia em tese, objeções e sequência argumentativa.
- **Pesquisar:** identifica lacunas, palavras-chave e fontes necessárias.
- **Revisar:** avalia clareza, rigor, coerência teológica e excesso retórico.
- **Escrever:** produz rascunhos subordinados à voz e à carta editorial do autor.

## Fluxo editorial

1. Capturar uma intuição em `book/notes/` ou no MEMENTO privado.
2. Produzir um resumo público e desidentificado.
3. Criar ou revisar um ensaio em uma branch.
4. Rodar o agente nos modos Arquitetar e Revisar.
5. Conferir fontes e citações manualmente.
6. Abrir pull request e registrar a decisão editorial.

## Limite atual

Este MVP usa busca textual no Supabase. A migração já inclui uma coluna vetorial opcional; a ingestão de embeddings será adicionada somente após escolher um modelo único e fixar sua dimensionalidade.