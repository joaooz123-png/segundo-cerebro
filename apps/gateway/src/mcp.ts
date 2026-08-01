import { McpServer } from '@modelcontextprotocol/sdk/server/mcp.js';
import { StdioServerTransport } from '@modelcontextprotocol/sdk/server/stdio.js';
import { z } from 'zod';
import { createAgentRegistry } from './agents/registry.js';
import { TaskSchema } from './domain/task.js';
import { TaskDispatcher } from './queue/dispatcher.js';
import { TaskStore } from './queue/task-store.js';

const store = new TaskStore();
const dispatcher = new TaskDispatcher(store, createAgentRegistry(), {
  githubToken: process.env.GITHUB_TOKEN
});

const server = new McpServer({
  name: 'rg-knowledge-os',
  version: '0.1.0'
});

server.tool(
  'submit_task',
  'Submit a structured task to an RG Knowledge OS agent.',
  { task: TaskSchema },
  async ({ task }) => {
    const record = dispatcher.submit(task);
    return { content: [{ type: 'text', text: JSON.stringify(record, null, 2) }] };
  }
);

server.tool(
  'get_task',
  'Retrieve one task by ID.',
  { taskId: z.string().min(1) },
  async ({ taskId }) => {
    const record = store.get(taskId);
    if (!record) {
      return { isError: true, content: [{ type: 'text', text: 'task_not_found' }] };
    }
    return { content: [{ type: 'text', text: JSON.stringify(record, null, 2) }] };
  }
);

server.tool(
  'list_tasks',
  'List submitted tasks, optionally filtered by status.',
  { status: z.enum(['queued', 'running', 'awaiting_approval', 'completed', 'failed', 'cancelled']).optional() },
  async ({ status }) => ({
    content: [{ type: 'text', text: JSON.stringify(store.list(status), null, 2) }]
  })
);

const transport = new StdioServerTransport();
await server.connect(transport);
