import { runBookAgent } from "@/lib/agent";
import type { AgentMode } from "@/lib/prompts";

const allowedModes = new Set<AgentMode>([
  "arquitetar",
  "pesquisar",
  "revisar",
  "escrever",
]);

export async function POST(request: Request): Promise<Response> {
  try {
    const body = (await request.json()) as {
      prompt?: unknown;
      mode?: unknown;
    };

    const prompt = typeof body.prompt === "string" ? body.prompt.trim() : "";
    const mode =
      typeof body.mode === "string" && allowedModes.has(body.mode as AgentMode)
        ? (body.mode as AgentMode)
        : "arquitetar";

    if (prompt.length < 5) {
      return Response.json(
        { error: "Descreva a ideia ou o trecho com pelo menos 5 caracteres." },
        { status: 400 },
      );
    }

    if (prompt.length > 20_000) {
      return Response.json(
        { error: "O texto excede o limite de 20.000 caracteres deste MVP." },
        { status: 413 },
      );
    }

    const result = await runBookAgent({ prompt, mode });
    return Response.json(result);
  } catch (error) {
    const message = error instanceof Error ? error.message : "Erro inesperado.";
    return Response.json({ error: message }, { status: 500 });
  }
}
