import type { AgentHandler } from './types.js';
import { codingAgent } from './coding-agent.js';

const placeholder = (role: string): AgentHandler => async (task) => ({
  accepted: true,
  role,
  taskId: task.taskId,
  action: task.action,
  next: `${role} implementation pending provider configuration`
});

export function createAgentRegistry(): Map<string, AgentHandler> {
  return new Map<string, AgentHandler>([
    ['planner', placeholder('planner')],
    ['retriever', placeholder('retriever')],
    ['verifier', placeholder('verifier')],
    ['composer', placeholder('composer')],
    ['archivist', placeholder('archivist')],
    ['coding', codingAgent]
  ]);
}
