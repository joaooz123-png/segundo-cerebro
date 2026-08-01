CREATE EXTENSION IF NOT EXISTS vector;
CREATE EXTENSION IF NOT EXISTS pgcrypto;

CREATE TABLE IF NOT EXISTS entities (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  kind text NOT NULL,
  canonical_name text NOT NULL,
  aliases jsonb NOT NULL DEFAULT '[]'::jsonb,
  metadata jsonb NOT NULL DEFAULT '{}'::jsonb,
  created_at timestamptz NOT NULL DEFAULT now(),
  updated_at timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS documents (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  external_id text,
  source text NOT NULL,
  title text NOT NULL,
  uri text,
  checksum text,
  captured_at timestamptz,
  metadata jsonb NOT NULL DEFAULT '{}'::jsonb,
  created_at timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS facts (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  case_key text,
  statement text NOT NULL,
  status text NOT NULL CHECK (status IN ('documented','reported','pending','hypothesis','disputed')),
  occurred_at timestamptz,
  confidence numeric(4,3),
  metadata jsonb NOT NULL DEFAULT '{}'::jsonb,
  embedding vector(768),
  created_at timestamptz NOT NULL DEFAULT now(),
  updated_at timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS fact_documents (
  fact_id uuid NOT NULL REFERENCES facts(id) ON DELETE CASCADE,
  document_id uuid NOT NULL REFERENCES documents(id) ON DELETE CASCADE,
  locator text,
  PRIMARY KEY (fact_id, document_id)
);

CREATE TABLE IF NOT EXISTS fact_entities (
  fact_id uuid NOT NULL REFERENCES facts(id) ON DELETE CASCADE,
  entity_id uuid NOT NULL REFERENCES entities(id) ON DELETE CASCADE,
  relation text NOT NULL,
  PRIMARY KEY (fact_id, entity_id, relation)
);

CREATE TABLE IF NOT EXISTS corrections (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  scope text NOT NULL,
  rule text NOT NULL,
  priority integer NOT NULL DEFAULT 100,
  active boolean NOT NULL DEFAULT true,
  created_at timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS context_packs (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  request text NOT NULL,
  coverage numeric(5,2) NOT NULL,
  payload jsonb NOT NULL,
  conflicts jsonb NOT NULL DEFAULT '[]'::jsonb,
  omissions jsonb NOT NULL DEFAULT '[]'::jsonb,
  created_at timestamptz NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS facts_case_key_idx ON facts(case_key);
CREATE INDEX IF NOT EXISTS facts_status_idx ON facts(status);
CREATE INDEX IF NOT EXISTS facts_embedding_idx ON facts USING hnsw (embedding vector_cosine_ops);
CREATE INDEX IF NOT EXISTS entities_name_idx ON entities(canonical_name);
