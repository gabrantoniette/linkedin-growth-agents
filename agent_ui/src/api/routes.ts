export const APIRoutes = {
  GetAgents: (agentOSUrl: string) => `${agentOSUrl}/agents`,
  AgentRun: (agentOSUrl: string) => `${agentOSUrl}/agents/{agent_id}/runs`,
  Status: (agentOSUrl: string) => `${agentOSUrl}/health`,
  GetSessions: (agentOSUrl: string) => `${agentOSUrl}/sessions`,
  GetSession: (agentOSUrl: string, sessionId: string) =>
    `${agentOSUrl}/sessions/${sessionId}/runs`,

  DeleteSession: (agentOSUrl: string, sessionId: string) =>
    `${agentOSUrl}/sessions/${sessionId}`,

  GetTeams: (agentOSUrl: string) => `${agentOSUrl}/teams`,
  TeamRun: (agentOSUrl: string, teamId: string) =>
    `${agentOSUrl}/teams/${teamId}/runs`,
  // This UI was written for Agno 2.x, which served under /v1. In AgentOS 3.0 the
  // session route is the same for an agent and a team, with no version prefix.
  DeleteTeamSession: (agentOSUrl: string, _teamId: string, sessionId: string) =>
    `${agentOSUrl}/sessions/${sessionId}`,

  // Resumes a run that paused for approval. The reply is another SSE stream, so
  // the caller feeds it through the same chunk handler as the original run.
  TeamContinueRun: (agentOSUrl: string, teamId: string, runId: string) =>
    `${agentOSUrl}/teams/${teamId}/runs/${runId}/continue`,
  AgentContinueRun: (agentOSUrl: string, agentId: string, runId: string) =>
    `${agentOSUrl}/agents/${agentId}/runs/${runId}/continue`
}
