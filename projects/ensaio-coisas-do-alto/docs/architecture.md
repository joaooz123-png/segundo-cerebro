# Arquitetura do agente editorial

## Objetivo

Reduzir o esforço mecânico de pesquisa, recuperação de contexto, estruturação e revisão sem terceirizar autoria, discernimento ou publicação.

## Componentes

```text
Leitor/Autor
    |
    v
Next.js UI (Vercel)
    |
    v
/api/agent
    |
    +--> Agente editorial: prompt, limite de etapas, ferramentas e guardrails
    |       |
    |       +--> Hugging Face Inference Providers
    |       |
    |       +--> search_memory
    |               |
    |               v
    |          Supabase RPC + RLS
    |
    v
Resposta não publicada
```

## Fontes canônicas

| Camada | Função | Exposição |
|---|---|---|
| Wisebase/MEMENTO | memória privada, continuidade e microcards | privada |
| GitHub/Markdown | manuscrito, decisões e arquitetura revisadas | pública |
| Supabase `book_chunks` | trechos públicos recuperáveis pelo agente | pública somente quando `is_public=true` |
| Fontes externas | pesquisa verificável e bibliografia | pública, com metadados |

## Decisão de segurança

A aplicação usa apenas a chave publicável do Supabase. O banco concede ao público somente `SELECT` em linhas explicitamente publicadas. Não existe ferramenta pública de escrita, atualização ou exclusão.

Uma futura área administrativa deverá exigir autenticação e políticas de propriedade. Ela não deve reutilizar a política pública.

## Ciclo agentivo

O agente pode executar até quatro iterações:

1. interpretar a demanda conforme o modo editorial;
2. decidir se precisa consultar o mapa do livro ou a memória pública;
3. executar a ferramenta e incorporar o resultado como fonte não confiável;
4. concluir com resposta revisável ou declarar lacunas.

Se o provedor não suportar tool-calling, o agente retorna ao modo direto e deve declarar a ausência de memória recuperada.

## Busca

### MVP

Full-text search em português com `tsvector`, GIN e uma função RPC protegida por RLS.

### Evolução

- fixar um único modelo de embeddings de 384 dimensões;
- gerar embeddings no momento de publicação;
- combinar busca lexical e vetorial;
- registrar avaliação de relevância;
- criar conjunto de perguntas de teste para cada capítulo.

Embeddings de modelos diferentes nunca devem compartilhar a mesma coluna vetorial.

## Agentes futuros

A arquitetura pode evoluir para uma pequena equipe especializada:

- **Cartógrafo:** mantém mapa de capítulos, teses e dependências.
- **Pesquisador:** propõe fontes primárias e contraexemplos.
- **Crítico:** procura falhas, sentimentalismo e saltos lógicos.
- **Editor:** melhora ritmo, clareza e continuidade.
- **Bibliotecário:** ingere somente conteúdo aprovado e registra proveniência.

O orquestrador deve impedir que um agente publique diretamente o produto de outro.

## Critérios de qualidade

- nenhuma citação inventada;
- toda alegação verificável possui fonte ou marcador de pendência;
- conteúdo privado não aparece em logs, banco público ou commits;
- o agente identifica a melhor objeção à tese;
- o texto final mantém decisão humana explícita;
- alterações no manuscrito passam por pull request.
