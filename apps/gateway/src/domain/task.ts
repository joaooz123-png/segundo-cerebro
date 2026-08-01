import { z } from 'zod';

export const AgentNameSchema = z.enum([
  'retriever',
  'planner',
  'verifier',
  'composer',
  'archivist',
  'coding'
]);

export const TaskStatusSchema = z.enum([
  'queued',
  'running',
  'awaiting_approval',
  'completed',
  'failed',
  'cancelled'
]);

export const TaskSchema = z.object({
  taskId: z.string().min(1),
  agent: AgentNameSchema,
  action: z.string().min(1),
  contextPackId: z.string().optional(),
  repository: z.string().optional(),
  branch: z.string().optional(),
  payload: z.record(z.unknown()).default({}),
  approvalRequired: z.boolean().default(true),
  createdBy: z.string().default('chatgpt'),
  createdAt: z.string().datetime().optional()
});

export type TaskInput = z.infer<typeof TaskSchema>;
export type TaskStatus = z.infer<typeof TaskStatusSchema>;

export interface TaskRecord extends TaskInput {
  status: TaskStatus;
  createdAt: string;
  updatedAt: string;
  result?: unknown;
  error?: string;
}
