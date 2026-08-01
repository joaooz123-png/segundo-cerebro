import { Octokit } from '@octokit/rest';
import type { AgentHandler } from './types.js';

function parseRepository(repository?: string): { owner: string; repo: string } {
  if (!repository || !repository.includes('/')) throw new Error('repository_required');
  const [owner, repo] = repository.split('/', 2);
  if (!owner || !repo) throw new Error('invalid_repository');
  return { owner, repo };
}

export const codingAgent: AgentHandler = async (task, context) => {
  if (!context.githubToken) {
    return {
      accepted: false,
      taskId: task.taskId,
      status: 'awaiting_configuration',
      required: ['GITHUB_TOKEN'],
      next: 'configure a fine-grained token with repository contents and pull-request permissions'
    };
  }

  const { owner, repo } = parseRepository(task.repository);
  const octokit = new Octokit({ auth: context.githubToken });
  const repository = await octokit.repos.get({ owner, repo });
  const baseBranch = String(task.payload.baseBranch ?? repository.data.default_branch);
  const branch = task.branch ?? `agent/${task.taskId.toLowerCase()}`;
  const baseRef = await octokit.git.getRef({ owner, repo, ref: `heads/${baseBranch}` });

  try {
    await octokit.git.createRef({
      owner,
      repo,
      ref: `refs/heads/${branch}`,
      sha: baseRef.data.object.sha
    });
  } catch (error: unknown) {
    const status = typeof error === 'object' && error && 'status' in error ? Number(error.status) : undefined;
    if (status !== 422) throw error;
  }

  const issueBody = [
    `Task ID: ${task.taskId}`,
    `Agent: coding`,
    `Action: ${task.action}`,
    `Branch: ${branch}`,
    task.contextPackId ? `Context Pack: ${task.contextPackId}` : undefined,
    '',
    '## Payload',
    '```json',
    JSON.stringify(task.payload, null, 2),
    '```',
    '',
    '## Contract',
    '- Work only on the branch above.',
    '- Run lint, tests and type checks.',
    '- Open a pull request; do not merge automatically.',
    '- Report changed files, risks and residual work.'
  ].filter(Boolean).join('\n');

  const issue = await octokit.issues.create({
    owner,
    repo,
    title: `[coding-agent] ${task.action}`,
    body: issueBody
  });

  return {
    accepted: true,
    taskId: task.taskId,
    repository: `${owner}/${repo}`,
    baseBranch,
    branch,
    issueNumber: issue.data.number,
    issueUrl: issue.data.html_url,
    approvalRequired: true,
    next: 'coding agent implements the scoped change and opens a pull request'
  };
};
