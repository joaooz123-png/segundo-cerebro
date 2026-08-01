import type { TaskRecord } from '../domain/task.js';

export interface AgentContext {
  githubToken?: string;
}

export type AgentHandler = (task: TaskRecord, context: AgentContext) => Promise<unknown>;
