import type { AgentContext, AgentHandler } from '../agents/types.js';
import type { TaskInput, TaskRecord } from '../domain/task.js';
import { TaskStore } from './task-store.js';

export class TaskDispatcher {
  constructor(
    private readonly store: TaskStore,
    private readonly agents: Map<string, AgentHandler>,
    private readonly context: AgentContext
  ) {}

  submit(input: TaskInput): TaskRecord {
    const record = this.store.create(input);
    queueMicrotask(() => void this.run(record.taskId));
    return record;
  }

  async run(taskId: string): Promise<TaskRecord> {
    const task = this.store.get(taskId);
    if (!task) throw new Error('task_not_found');
    const handler = this.agents.get(task.agent);
    if (!handler) return this.store.update(taskId, { status: 'failed', error: 'agent_not_registered' });

    this.store.update(taskId, { status: 'running' });
    try {
      const result = await handler(task, this.context);
      const awaitingApproval = task.approvalRequired && task.agent === 'coding';
      return this.store.update(taskId, {
        status: awaitingApproval ? 'awaiting_approval' : 'completed',
        result
      });
    } catch (error) {
      const message = error instanceof Error ? error.message : String(error);
      return this.store.update(taskId, { status: 'failed', error: message });
    }
  }
}
