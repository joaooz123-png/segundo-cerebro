import { BOOK_MAP, buildSystemPrompt, type AgentMode } from "@/lib/prompts";
import { getPublicSupabase } from "@/lib/supabase";

type ToolCall = {
  id: string;
  type: "function";
  function: { name: string; arguments: string };
};

type Message = {
  role: "system" | "user" | "assistant" | "tool";
  content: string | null;
  tool_call_id?: string;
  tool_calls?: ToolCall[];
};

type CompletionResponse = {
  choices?: Array<{
    message?: {
      content?: string | null;
      tool_calls?: ToolCall[];
    };
  }>;
  error?: { message?: string };
};

const tools = [
  {
    type: "function",
    function: {
      name: "search_memory",
      description:
        "Busca apenas trechos públicos e revisados do projeto editorial. Use para recuperar conceitos, capítulos e decisões já registradas.",
      parameters: {
        type: "object",
        properties: {
          query: { type: "string", description: "Consulta curta em português" },
          limit: { type: "integer", minimum: 1, maximum: 8 },
        },
        required: ["query"],
        additionalProperties: false,
      },
    },
  },
  {
    type: "function",
    function: {
      name: "inspect_book_map",
      description: "Recupera o mapa provisório de capítulos do livro.",
      parameters: { type: "object", properties: {}, additionalProperties: false },
    },
  },
] as const;

async function executeTool(call: ToolCall): Promise<unknown> {
  let args: Record<string, unknown> = {};
  try {
    args = JSON.parse(call.function.arguments || "{}");
  } catch {
    return { ok: false, error: "Argumentos de ferramenta inválidos." };
  }

  if (call.function.name === "inspect_book_map") {
    return { ok: true, chapters: BOOK_MAP };
  }

  if (call.function.name === "search_memory") {
    const query = typeof args.query === "string" ? args.query.trim() : "";
    const limit = Math.min(Math.max(Number(args.limit) || 5, 1), 8);
    if (!query) return { ok: false, error: "Consulta vazia." };

    const supabase = getPublicSupabase();
    if (!supabase) {
      return {
        ok: false,
        error: "Supabase ainda não configurado; prossiga sem memória persistente.",
      };
    }

    const { data, error } = await supabase.rpc("search_public_book_chunks", {
      search_query: query,
      match_count: limit,
    });

    if (error) return { ok: false, error: error.message };
    return { ok: true, results: data ?? [] };
  }

  return { ok: false, error: `Ferramenta desconhecida: ${call.function.name}` };
}

async function callModel(messages: Message[], withTools: boolean): Promise<CompletionResponse> {
  const token = process.env.HF_TOKEN;
  if (!token) throw new Error("HF_TOKEN não configurado.");

  const model = process.env.HF_MODEL || "Qwen/Qwen3-4B-Instruct-2507";
  const response = await fetch("https://router.huggingface.co/v1/chat/completions", {
    method: "POST",
    headers: {
      Authorization: `Bearer ${token}`,
      "Content-Type": "application/json",
    },
    body: JSON.stringify({
      model,
      messages,
      ...(withTools ? { tools, tool_choice: "auto" } : {}),
      temperature: 0.35,
      max_tokens: 1600,
    }),
    signal: AbortSignal.timeout(45000),
  });

  const payload = (await response.json()) as CompletionResponse;
  if (!response.ok) {
    throw new Error(payload.error?.message || `Falha no Hugging Face (${response.status}).`);
  }
  return payload;
}

export async function runBookAgent(input: {
  prompt: string;
  mode: AgentMode;
}): Promise<{ answer: string; steps: number; model: string }> {
  const messages: Message[] = [
    { role: "system", content: buildSystemPrompt(input.mode) },
    { role: "user", content: input.prompt },
  ];

  let toolCallingAvailable = true;

  for (let step = 1; step <= 4; step += 1) {
    let completion: CompletionResponse;
    try {
      completion = await callModel(messages, toolCallingAvailable);
    } catch (error) {
      if (toolCallingAvailable) {
        toolCallingAvailable = false;
        messages.push({
          role: "system",
          content:
            "O provedor atual não aceitou ferramentas. Continue sem ferramentas e declare qualquer lacuna de memória ou fonte.",
        });
        continue;
      }
      throw error;
    }

    const assistant = completion.choices?.[0]?.message;
    if (!assistant) throw new Error("O modelo não retornou uma mensagem válida.");

    const toolCalls = assistant.tool_calls ?? [];
    if (toolCalls.length === 0) {
      const answer = assistant.content?.trim();
      if (!answer) throw new Error("O modelo retornou uma resposta vazia.");
      return {
        answer,
        steps: step,
        model: process.env.HF_MODEL || "Qwen/Qwen3-4B-Instruct-2507",
      };
    }

    messages.push({
      role: "assistant",
      content: assistant.content ?? null,
      tool_calls: toolCalls,
    });

    for (const call of toolCalls) {
      const output = await executeTool(call);
      messages.push({
        role: "tool",
        tool_call_id: call.id,
        content: JSON.stringify(output),
      });
    }
  }

  throw new Error("O agente atingiu o limite de etapas sem concluir a resposta.");
}
