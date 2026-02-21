import { makeRequest } from './utils'
import {
  SCOPE_TEST_CASES,
  PLACEHOLDER_USER_ID,
  PLACEHOLDER_GROUP_ID,
  PLACEHOLDER_TEAM_ID,
  PLACEHOLDER_KB_ID,
  PLACEHOLDER_CONNECTOR_ID,
  PLACEHOLDER_AGENT_ID,
  PLACEHOLDER_CONV_ID,
  type ScopeTestCase,
} from './scope-test-cases'

export type { ScopeTestCase }
export {
  ORG_TEST_CASES,
  USERS_TEST_CASES,
  USER_GROUPS_TEST_CASES,
  TEAMS_TEST_CASES,
  KB_TEST_CASES,
  SEARCH_TEST_CASES,
  CONVERSATIONS_TEST_CASES,
  AGENTS_TEST_CASES,
  CONNECTORS_TEST_CASES,
  SCOPE_TEST_CASES,
} from './scope-test-cases'

export interface ScopeTestResult {
  case: ScopeTestCase
  status: number
  passed: boolean
  message: string
}


function toId(value: unknown): string | null {
  if (value == null) return null
  if (typeof value === 'string' && value.length > 0) return value
  if (typeof value === 'object' && typeof (value as { toString?: () => string }).toString === 'function') {
    return (value as { toString: () => string }).toString()
  }
  return String(value)
}

function firstIdFromList(data: unknown): string | null {
  if (!data || typeof data !== 'object') return null
  const obj = data as Record<string, unknown>
  const list = Array.isArray(data)
    ? data
    : (obj.data ?? obj.users ?? obj.teams ?? obj.userGroups) as unknown[] | undefined
  if (!Array.isArray(list) || list.length === 0) return null
  const first = list[0] as Record<string, unknown>
  const id = first?.id ?? first?._id
  return id ? toId(id) : null
}

export async function fetchRealIds(
  baseUrl: string,
  accessToken: string,
): Promise<{ userId: string | null; groupId: string | null; teamId: string | null }> {
  const headers = { Authorization: `Bearer ${accessToken}` }
  let userId: string | null = null
  let groupId: string | null = null
  let teamId: string | null = null

  try {
    const res = await makeRequest<unknown>(`${baseUrl}/api/v1/users`, { headers })
    if (res.status === 200) userId = firstIdFromList(res.data)
  } catch {}
  try {
    const res = await makeRequest<unknown>(`${baseUrl}/api/v1/userGroups`, { headers })
    if (res.status === 200) groupId = firstIdFromList(res.data)
  } catch {}
  try {
    const res = await makeRequest<unknown>(`${baseUrl}/api/v1/teams?page=1&limit=10`, { headers })
    if (res.status === 200) teamId = firstIdFromList(res.data)
  } catch {}

  return { userId, groupId, teamId }
}

export function buildPathReplace(ids: {
  userId: string | null
  groupId: string | null
  teamId: string | null
}): Record<string, string> {
  return {
    [PLACEHOLDER_USER_ID]: ids.userId ?? PLACEHOLDER_USER_ID,
    [PLACEHOLDER_GROUP_ID]: ids.groupId ?? PLACEHOLDER_GROUP_ID,
    [PLACEHOLDER_TEAM_ID]: ids.teamId ?? PLACEHOLDER_TEAM_ID,
    [PLACEHOLDER_KB_ID]: PLACEHOLDER_KB_ID,
    [PLACEHOLDER_CONNECTOR_ID]: PLACEHOLDER_CONNECTOR_ID,
    [PLACEHOLDER_AGENT_ID]: PLACEHOLDER_AGENT_ID,
    [PLACEHOLDER_CONV_ID]: PLACEHOLDER_CONV_ID,
  }
}

export async function callScopeEndpoint(
  baseUrl: string,
  accessToken: string,
  testCase: ScopeTestCase,
  pathReplace: Record<string, string>,
): Promise<{ status: number }> {
  let path = testCase.path
  for (const [placeholder, realId] of Object.entries(pathReplace)) {
    path = path.replace(placeholder, realId)
  }

  const query = testCase.query
    ? '?' + Object.entries(testCase.query).map(([k, v]) => `${encodeURIComponent(k)}=${encodeURIComponent(String(v))}`).join('&')
    : ''

  const url = `${baseUrl.replace(/\/$/, '')}${path}${query}`
  const body = testCase.method === 'GET' ? undefined : (testCase.body ?? '{}')

  const res = await makeRequest<unknown>(url, {
    method: testCase.method,
    headers: {
      Authorization: `Bearer ${accessToken}`,
      ...(testCase.method !== 'GET' ? { 'Content-Type': 'application/json' } : {}),
    },
    body,
  })

  return { status: res.status }
}

/**
 * When token has required scope: 2xx or 4xx counts as pass.
 * When token does NOT have scope: we expect 403 (Forbidden). 401 is not treated as correct for missing scope.
 */
function getPassedAndMessage(hasScope: boolean, status: number): { passed: boolean; message: string } {
  if (hasScope) {
    if (status >= 200 && status < 300) return { passed: true, message: `OK (${status})` }
    if (status >= 400 && status < 500) return { passed: true, message: `Auth OK (${status})` }
    return { passed: false, message: `Unexpected ${status}` }
  }
  if (status === 403) return { passed: true, message: 'Correctly denied (403)' }
  return { passed: false, message: `Expected 403, got ${status}` }
}

export async function runScopeTests(
  backendUrl: string,
  accessToken: string,
  tokenScopes: string[],
): Promise<ScopeTestResult[]> {
  const baseUrl = backendUrl.replace(/\/$/, '')
  const ids = await fetchRealIds(baseUrl, accessToken)
  const pathReplace = buildPathReplace(ids)
  const results: ScopeTestResult[] = []

  for (const testCase of SCOPE_TEST_CASES) {
    const hasScope = tokenScopes.includes(testCase.requiredScope)

    try {
      const { status } = await callScopeEndpoint(baseUrl, accessToken, testCase, pathReplace)
      const { passed, message } = getPassedAndMessage(hasScope, status)
      results.push({ case: testCase, status, passed, message })
    } catch (err) {
      results.push({
        case: testCase,
        status: -1,
        passed: false,
        message: (err as Error).message,
      })
    }
  }

  return results
}

export function parseScopes(scopeString: string): string[] {
  if (!scopeString?.trim()) return []
  return scopeString.split(/\s+/).map((s) => s.trim()).filter(Boolean)
}
