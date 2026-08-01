const modules = [
  "Ingestão",
  "Casos",
  "Fatos",
  "Evidências",
  "Conflitos",
  "Context Packs",
  "Correções permanentes",
];

export default function Home() {
  return (
    <main style={{ maxWidth: 960, margin: "48px auto", fontFamily: "sans-serif" }}>
      <h1>RG Knowledge OS</h1>
      <p>Painel de recuperação, auditoria e continuidade.</p>
      <ul>
        {modules.map((module) => (
          <li key={module}>{module}</li>
        ))}
      </ul>
      <p>Persistência: Neon PostgreSQL + pgvector.</p>
    </main>
  );
}
