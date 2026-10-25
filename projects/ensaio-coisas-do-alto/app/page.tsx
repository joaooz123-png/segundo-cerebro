"use client";

import { FormEvent, useState } from "react";
import type { AgentMode } from "@/lib/prompts";

const modes: Array<{ value: AgentMode; label: string; description: string }> = [
  { value: "arquitetar", label: "Arquitetar", description: "Tese, estrutura, objeções e sequência." },
  { value: "pesquisar", label: "Pesquisar", description: "Lacunas, fontes e perguntas verificáveis." },
  { value: "revisar", label: "Revisar", description: "Crítica de clareza, rigor e coerência." },
  { value: "escrever", label: "Escrever", description: "Rascunho ensaístico revisável." },
];

type AgentResult = {
  answer?: string;
  error?: string;
  model?: string;
  steps?: number;
};

export default function HomePage() {
  const [mode, setMode] = useState<AgentMode>("arquitetar");
  const [prompt, setPrompt] = useState("");
  const [result, setResult] = useState<AgentResult>({});
  const [loading, setLoading] = useState(false);

  async function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setLoading(true);
    setResult({});

    try {
      const response = await fetch("/api/agent", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ prompt, mode }),
      });
      const data = (await response.json()) as AgentResult;
      setResult(data);
    } catch {
      setResult({ error: "Não foi possível conectar ao agente." });
    } finally {
      setLoading(false);
    }
  }

  return (
    <main>
      <header className="hero">
        <p className="eyebrow">Laboratório editorial público</p>
        <h1>Um Ensaio sobre as Coisas do Alto</h1>
        <p className="lead">
          Um agente para organizar intuições, confrontar argumentos, localizar lacunas e preservar a voz do autor.
        </p>
      </header>

      <section className="workspace" aria-label="Agente editorial">
        <form onSubmit={submit}>
          <div className="mode-grid">
            {modes.map((item) => (
              <label className={mode === item.value ? "mode active" : "mode"} key={item.value}>
                <input
                  type="radio"
                  name="mode"
                  value={item.value}
                  checked={mode === item.value}
                  onChange={() => setMode(item.value)}
                />
                <strong>{item.label}</strong>
                <span>{item.description}</span>
              </label>
            ))}
          </div>

          <label className="prompt-label" htmlFor="prompt">
            Ideia, pergunta ou trecho
          </label>
          <textarea
            id="prompt"
            value={prompt}
            onChange={(event) => setPrompt(event.target.value)}
            placeholder="Ex.: Quero desenvolver um ensaio sobre a diferença entre esperança cristã e otimismo psicológico..."
            minLength={5}
            maxLength={20000}
            required
          />

          <button type="submit" disabled={loading || prompt.trim().length < 5}>
            {loading ? "Pensando com método..." : "Executar agente"}
          </button>
        </form>

        <article className="answer" aria-live="polite">
          <div className="answer-heading">
            <h2>Resposta editorial</h2>
            {result.model ? <small>{result.model} · {result.steps} etapa(s)</small> : null}
          </div>
          {result.error ? <p className="error">{result.error}</p> : null}
          {result.answer ? <div className="answer-text">{result.answer}</div> : null}
          {!result.error && !result.answer ? (
            <p className="empty">A resposta aparecerá aqui. Nenhum conteúdo é publicado automaticamente.</p>
          ) : null}
        </article>
      </section>

      <footer>
        Memória privada no MEMENTO. Conteúdo público apenas após revisão humana e versionamento no GitHub.
      </footer>
    </main>
  );
}
