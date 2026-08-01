import Fastify from 'fastify';
import { z } from 'zod';
import { createAgentRegistry } from './agents/registry.js';
import { TaskSchema, TaskStatusSchema } from './domain/task.js';
import { TaskDispatcher } from './queue/dispatcher.js';
import { TaskStore } from './queue/task-store.js';

const app = Fastify({ logger: true });
const store = new TaskStore();
const agents = createAgentRegistry();
const dispatcher = new TaskDispatcher(store, agents, {
  githubToken: process.env.GITHUB_TOKEN
});

app.get('/health', async () => ({
  status: 'ok',
  service: 'rg-knowledge-node-gateway',
  agents: [...agents.keys()],
  queue: {
    total: store.list().length,
    queued: store.list('queued').length,
    running: store.list('running').length
  }
}));

app.post('/v1/tasks', async (request, reply) => {
  const parsed = TaskSchema.safeParse(request.body);
  if (!parsed.success) {
    return reply.code(400).send({ error: 'invalid_task', details: parsed.error.flatten() });
  }

  try {
    const record = dispatcher.submit(parsed.data);
    return reply.code(202).send(record);
  } catch (error) {
    const message = error instanceof Error ? error.message : String(error);
    const status = message === 'task_already_exists' ? 409 : 500;
    return reply.code(status).send({ error: message });
  }
});

app.get('/v1/tasks', async (request, reply) => {
  const query = z.object({ status: TaskStatusSchema.optional() }).safeParse(request.query);
  if (!query.success) return reply.code(400).send({ error: 'invalid_query' });
  return store.list(query.data.status);
});

app.get('/v1/tasks/:taskId', async (request, reply) => {
  const params = z.object({ taskId: z.string().min(1) }).safeParse(request.params);
  if (!params.success) return reply.code(400).send({ error: 'invalid_task_id' });
  const record = store.get(params.data.taskId);
  if (!record) return reply.code(404).send({ error: 'task_not_found' });
  return record;
});

const port = Number(process.env.PORT ?? 3100);
const host = process.env.HOST ?? '0.0.0.0';

app.listen({ port, host }).catch((error) => {
  app.log.error(error);
  process.exit(1);
});
