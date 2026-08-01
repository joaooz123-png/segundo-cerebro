import type { TaskInput, TaskRecord, TaskStatus } from '../domain/task.js';

export class TaskStore {
  private readonly tasks = new Map<string, TaskRecord>();

  create(input: TaskInput): TaskRecord {
    if (this.tasks.has(input.taskId)) throw new Error('task_already_exists');
    const now = new Date().toISOString();
    const record: TaskRecord = {
      ...input,
      createdAt: input.createdAt ?? now,
      updatedAt: now,
      status: 'queued'
    };
    this.tasks.set(record.taskId, record);
    return structuredClone(record);
  }

  get(taskId: string): TaskRecord | undefined {
    const record = this.tasks.get(taskId);
    return record ? structuredClone(record) : undefined;
  }

  list(status?: TaskStatus): TaskRecord[] {
    return [...this.tasks.values()]
      .filter((task) => !status || task.status === status)
      .sort((a, b) => b.createdAt.localeCompare(a.createdAt))
      .map((task) => structuredClone(task));
  }

  update(taskId: string, patch: Partial<Pick<TaskRecord, 'status' | 'result' | 'error'>>): TaskRecord {
    const current = this.tasks.get(taskId);
    if (!current) throw new Error('task_not_found');
    const updated: TaskRecord = {
      ...current,
      ...patch,
      updatedAt: new Date().toISOString()
    };
    this.tasks.set(taskId, updated);
    return structuredClone(updated);
  }
}
