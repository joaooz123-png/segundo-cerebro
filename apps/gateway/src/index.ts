import Fastify from 'fastify';
import { z } from 'zod';

const app = Fastify({ logger: true });

const TaskSchema = z.object({
  taskId: z.string().min(1),
  agent: z.enum(['retriever', 'planner', 'verifier', 'composer', 'archivist', 'coding']),
  action: z.string().min(1),
  contextPackId: z.string().optional(),
  repository: z.string().optional(),
  branch: z.string().optional(),
  payload: z.record(z.unknown()).default({}),
  approvalRequired: z.boolean().default(true)
});

type Task = z.infer<typeof TaskSchema>;

const agentRegistry = new Map<string, (task: Task) => Promise<unknown>>();

agentRegistry.set('retriever', async (task) => ({
  accepted: true,
  role: 'retriever',
  taskId: task.taskId,
  next: 'query configured sources and build a context pack'
}));

agentRegistry.set('coding', async (task) => ({
  accepted: true,
  role: 'coding',
  taskId: task.taskId,
  repository: task.repository,
  branch: task.branch,
  next: 'create an isolated branch, implement the scoped change, run checks, and open a PR'
}));

app.get('/health', async () => ({
  status: 'ok',
  service: 'rg-knowledge-node-gateway',
  agents: [...agentRegistry.keys()]
}));

app.post('/v1/tasks', async (request, reply) => {
  const parsed = TaskSchema.safeParse(request.body);
  if (!parsed.success) {
    return reply.code(400).send({ error: 'invalid_task', details: parsed.error.flatten() });
  }

  const handler = agentRegistry.get(parsed.data.agent);
  if (!handler) return reply.code(404).send({ error: 'agent_not_registered' });

  const result = await handler(parsed.data);
  return reply.code(202).send(result);
});

const port = Number(process.env.PORT ?? 3100);
const host = process.env.HOST ?? '0.0.0.0';

app.listen({ port, host }).catch((error) => {
  app.log.error(error);
  process.exit(1);
});
