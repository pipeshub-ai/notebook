
export const PLACEHOLDER_USER_ID = '__USER_ID__'
export const PLACEHOLDER_GROUP_ID = '__GROUP_ID__'
export const PLACEHOLDER_TEAM_ID = '__TEAM_ID__'
export const PLACEHOLDER_KB_ID = '__KB_ID__'
export const PLACEHOLDER_CONNECTOR_ID = '__CONNECTOR_ID__'
export const PLACEHOLDER_AGENT_ID = '__AGENT_ID__'
export const PLACEHOLDER_CONV_ID = '__CONV_ID__'

export interface ScopeTestCase {
  id: string
  name: string
  method: 'GET' | 'POST' | 'PUT' | 'PATCH' | 'DELETE'
  path: string
  requiredScope: string
  category: 'Organization' | 'Users' | 'User Groups' | 'Teams' | 'Knowledge Base' | 'Search' | 'Conversations' | 'Agents' | 'Connectors'
  query?: Record<string, string | number>
  body?: string
}

export const ORG_TEST_CASES: ScopeTestCase[] = [
  {
    id: 'org-get',
    name: 'Get Organization',
    method: 'GET',
    path: '/api/v1/org',
    requiredScope: 'org:read',
    category: 'Organization',
  },
  {
    id: 'org-put',
    name: 'Update Organization',
    method: 'PUT',
    path: '/api/v1/org',
    requiredScope: 'org:write',
    category: 'Organization',
  },
  {
    id: 'org-delete',
    name: 'Delete Organization',
    method: 'DELETE',
    path: '/api/v1/org',
    requiredScope: 'org:admin',
    category: 'Organization',
  },
]

export const USERS_TEST_CASES: ScopeTestCase[] = [
  {
    id: 'users-list',
    name: 'List Users',
    method: 'GET',
    path: '/api/v1/users',
    requiredScope: 'user:read',
    category: 'Users',
  },
  {
    id: 'users-get-id',
    name: 'Get User by ID',
    method: 'GET',
    path: `/api/v1/users/${PLACEHOLDER_USER_ID}`,
    requiredScope: 'user:read',
    category: 'Users',
  },
  {
    id: 'users-post',
    name: 'Create User (invite)',
    method: 'POST',
    path: '/api/v1/users',
    requiredScope: 'user:invite',
    category: 'Users',
    body: '{"fullName":"User","email":"user@example.com"}',
  },
  {
    id: 'users-put-id',
    name: 'Update User',
    method: 'PUT',
    path: `/api/v1/users/${PLACEHOLDER_USER_ID}`,
    requiredScope: 'user:write',
    category: 'Users',
    body: '{"fullName":"User Updated"}',
  },
  {
    id: 'users-delete-id',
    name: 'Delete User',
    method: 'DELETE',
    path: `/api/v1/users/${PLACEHOLDER_USER_ID}`,
    requiredScope: 'user:delete',
    category: 'Users',
  },
]

export const USER_GROUPS_TEST_CASES: ScopeTestCase[] = [
  {
    id: 'usergroups-list',
    name: 'List User Groups',
    method: 'GET',
    path: '/api/v1/userGroups',
    requiredScope: 'usergroup:read',
    category: 'User Groups',
  },
  {
    id: 'usergroups-post',
    name: 'Create User Group',
    method: 'POST',
    path: '/api/v1/userGroups',
    requiredScope: 'usergroup:write',
    category: 'User Groups',
    body: '{"name":"Group","type":"default"}',
  },
  {
    id: 'usergroups-put-id',
    name: 'Update User Group',
    method: 'PUT',
    path: `/api/v1/userGroups/${PLACEHOLDER_GROUP_ID}`,
    requiredScope: 'usergroup:write',
    category: 'User Groups',
    body: '{"name":"Group Updated","type":"default"}',
  },
]

export const TEAMS_TEST_CASES: ScopeTestCase[] = [
  {
    id: 'teams-list',
    name: 'List Teams',
    method: 'GET',
    path: '/api/v1/teams',
    requiredScope: 'team:read',
    category: 'Teams',
    query: { page: 1, limit: 10 },
  },
  {
    id: 'teams-post',
    name: 'Create Team',
    method: 'POST',
    path: '/api/v1/teams',
    requiredScope: 'team:write',
    category: 'Teams',
    body: '{"name":"Team"}',
  },
  {
    id: 'teams-put-id',
    name: 'Update Team',
    method: 'PUT',
    path: `/api/v1/teams/${PLACEHOLDER_TEAM_ID}`,
    requiredScope: 'team:write',
    category: 'Teams',
    body: '{"name":"Team Updated"}',
  },
]

export const KB_TEST_CASES: ScopeTestCase[] = [
  {
    id: 'kb-get',
    name: 'Get Knowledge Base',
    method: 'GET',
    path: `/api/v1/knowledgeBase/${PLACEHOLDER_KB_ID}`,
    requiredScope: 'kb:read',
    category: 'Knowledge Base',
  },
  {
    id: 'kb-post',
    name: 'Create Knowledge Base',
    method: 'POST',
    path: '/api/v1/knowledgeBase',
    requiredScope: 'kb:write',
    category: 'Knowledge Base',
    body: '{"name":"Test KB"}',
  },
  {
    id: 'kb-put-id',
    name: 'Update Knowledge Base',
    method: 'PUT',
    path: `/api/v1/knowledgeBase/${PLACEHOLDER_KB_ID}`,
    requiredScope: 'kb:write',
    category: 'Knowledge Base',
    body: '{"name":"Test KB Updated"}',
  },
  {
    id: 'kb-delete-id',
    name: 'Delete Knowledge Base',
    method: 'DELETE',
    path: `/api/v1/knowledgeBase/${PLACEHOLDER_KB_ID}`,
    requiredScope: 'kb:delete',
    category: 'Knowledge Base',
  },
  {
    id: 'kb-upload',
    name: 'Upload to Knowledge Base',
    method: 'POST',
    path: `/api/v1/knowledgeBase/${PLACEHOLDER_KB_ID}/upload`,
    requiredScope: 'kb:upload',
    category: 'Knowledge Base',
    body: '{}',
  },
]

export const SEARCH_TEST_CASES: ScopeTestCase[] = [
  {
    id: 'search-query',
    name: 'Execute Search',
    method: 'POST',
    path: '/api/v1/search',
    requiredScope: 'search:query',
    category: 'Search',
    body: '{"query":"test"}',
  },
  {
    id: 'search-semantic',
    name: 'Semantic Search',
    method: 'POST',
    path: '/api/v1/search/semantic',
    requiredScope: 'search:semantic',
    category: 'Search',
    body: '{"query":"test"}',
  },
]

export const CONVERSATIONS_TEST_CASES: ScopeTestCase[] = [
  {
    id: 'conversations-list',
    name: 'List Conversations',
    method: 'GET',
    path: '/api/v1/conversations',
    requiredScope: 'conversation:read',
    category: 'Conversations',
  },
  {
    id: 'conversations-archives',
    name: 'Get Conversation Archives',
    method: 'GET',
    path: '/api/v1/conversations/show/archives',
    requiredScope: 'conversation:read',
    category: 'Conversations',
  },
  {
    id: 'conversations-create',
    name: 'Create Conversation',
    method: 'POST',
    path: '/api/v1/conversations/create',
    requiredScope: 'conversation:write',
    category: 'Conversations',
    body: '{}',
  },
  {
    id: 'conversations-put-id',
    name: 'Update Conversation',
    method: 'PUT',
    path: `/api/v1/conversations/${PLACEHOLDER_CONV_ID}`,
    requiredScope: 'conversation:write',
    category: 'Conversations',
    body: '{}',
  },
  {
    id: 'conversations-chat',
    name: 'Chat in Conversation',
    method: 'POST',
    path: `/api/v1/conversations/${PLACEHOLDER_CONV_ID}/chat`,
    requiredScope: 'conversation:chat',
    category: 'Conversations',
    body: '{"message":"hello"}',
  },
]

export const AGENTS_TEST_CASES: ScopeTestCase[] = [
  {
    id: 'agents-list',
    name: 'List Agents',
    method: 'GET',
    path: '/api/v1/agents',
    requiredScope: 'agent:read',
    category: 'Agents',
  },
  {
    id: 'agents-post',
    name: 'Create Agent',
    method: 'POST',
    path: '/api/v1/agents',
    requiredScope: 'agent:write',
    category: 'Agents',
    body: '{"name":"Test Agent"}',
  },
  {
    id: 'agents-put-id',
    name: 'Update Agent',
    method: 'PUT',
    path: `/api/v1/agents/${PLACEHOLDER_AGENT_ID}`,
    requiredScope: 'agent:write',
    category: 'Agents',
    body: '{"name":"Test Agent Updated"}',
  },
  {
    id: 'agents-execute',
    name: 'Execute Agent',
    method: 'POST',
    path: `/api/v1/agents/${PLACEHOLDER_AGENT_ID}/execute`,
    requiredScope: 'agent:execute',
    category: 'Agents',
    body: '{}',
  },
]

export const CONNECTORS_TEST_CASES: ScopeTestCase[] = [
  {
    id: 'connectors-list',
    name: 'List Connectors',
    method: 'GET',
    path: '/api/v1/connectors',
    requiredScope: 'connector:read',
    category: 'Connectors',
  },
  {
    id: 'connectors-registry',
    name: 'Get Connector Registry',
    method: 'GET',
    path: '/api/v1/connectors/registry',
    requiredScope: 'connector:read',
    category: 'Connectors',
  },
  {
    id: 'connectors-post',
    name: 'Create Connector',
    method: 'POST',
    path: '/api/v1/connectors',
    requiredScope: 'connector:write',
    category: 'Connectors',
    body: '{"type":"test"}',
  },
  {
    id: 'connectors-put-id',
    name: 'Update Connector',
    method: 'PUT',
    path: `/api/v1/connectors/${PLACEHOLDER_CONNECTOR_ID}`,
    requiredScope: 'connector:write',
    category: 'Connectors',
    body: '{}',
  },
  {
    id: 'connectors-sync',
    name: 'Sync Connector',
    method: 'POST',
    path: `/api/v1/connectors/${PLACEHOLDER_CONNECTOR_ID}/sync`,
    requiredScope: 'connector:sync',
    category: 'Connectors',
    body: '{}',
  },
  {
    id: 'connectors-delete-id',
    name: 'Delete Connector',
    method: 'DELETE',
    path: `/api/v1/connectors/${PLACEHOLDER_CONNECTOR_ID}`,
    requiredScope: 'connector:delete',
    category: 'Connectors',
  },
]

export const SCOPE_TEST_CASES: ScopeTestCase[] = [
  ...ORG_TEST_CASES,
  ...USERS_TEST_CASES,
  ...USER_GROUPS_TEST_CASES,
  ...TEAMS_TEST_CASES,
  ...KB_TEST_CASES,
  ...SEARCH_TEST_CASES,
  ...CONVERSATIONS_TEST_CASES,
  ...AGENTS_TEST_CASES,
  ...CONNECTORS_TEST_CASES,
]
