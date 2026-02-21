/**
 * Sample OAuth Client Server
 *
 * Demonstrates the complete OAuth 2.0 Authorization Code flow with PKCE for PipesHub.
 *
 * Usage:
 *   CLIENT_ID=xxx CLIENT_SECRET=xxx npm start
 */

import express, { Request, Response, NextFunction, Application } from 'express'
import { Server } from 'http'
import type {
  PendingAuthorization,
  TokenResponse,
  OAuthTokenError,
  RateLimitData,
  OAuthApp,
  OAuthAppsResponse,
} from './types'
import {
  makeRequest,
  generateCodeVerifier,
  generateCodeChallenge,
  generateState,
  maskSecret,
  escapeHtml,
  loadEnvFile,
} from './utils'
import { loadConfig, validateConfig } from './config'
import { runScopeTests, parseScopes, type ScopeTestResult } from './scope-test-runner'

// Load environment variables
loadEnvFile()

// Load and validate configuration
const config = loadConfig()
validateConfig(config)

const app: Application = express()
app.use(express.urlencoded({ extended: true }))
app.use(express.json())

// In-memory storage for PKCE and state (use Redis/DB in production)
const pendingAuthorizations = new Map<string, PendingAuthorization>()

// In-memory storage for user tokens (use session/DB in production)
let currentUserTokens: TokenResponse | null = null

// Simple in-memory rate limiter
const rateLimitMap = new Map<string, RateLimitData>()

function rateLimit(req: Request, res: Response, next: NextFunction): void | Response {
  const ip: string = req.ip || req.connection?.remoteAddress || 'unknown'
  const now: number = Date.now()
  const windowStart: number = now - config.rateLimit.windowMs

  // Clean up old entries
  for (const [key, data] of rateLimitMap.entries()) {
    if (data.windowStart < windowStart) {
      rateLimitMap.delete(key)
    }
  }

  const existing = rateLimitMap.get(ip)
  if (existing && existing.windowStart >= windowStart) {
    existing.count++
    if (existing.count > config.rateLimit.maxRequests) {
      return res.status(429).send(`
        <!DOCTYPE html>
        <html>
        <head><title>Too Many Requests</title></head>
        <body style="font-family: Arial, sans-serif; max-width: 600px; margin: 50px auto; padding: 20px;">
          <h1 style="color: #dc3545;">Too Many Requests</h1>
          <p>Please wait before trying again.</p>
          <a href="/admin">← Back to Admin</a>
        </body>
        </html>
      `)
    }
  } else {
    rateLimitMap.set(ip, { windowStart: now, count: 1 })
  }

  next()
}

// Server instance for graceful shutdown
let server: Server | null = null

console.log('Configuration:')
console.log('  Backend URL:', config.backend.url)
console.log('  Client ID:', maskSecret(config.oauth.clientId))
console.log('  Callback URL:', config.oauth.callbackUrl)
console.log('  Scopes (requested at login):', config.oauth.scopes)
console.log('')

/**
 * API endpoint to get current token (for test automation)
 */
app.get('/api/token', (req: Request, res: Response) => {
  if (!currentUserTokens) {
    return res.status(404).json({ error: 'No token available. Please log in first.' })
  }
  res.json({
    access_token: currentUserTokens.access_token,
    token_type: currentUserTokens.token_type,
    scope: currentUserTokens.scope,
    expires_in: currentUserTokens.expires_in,
  })
})

/**
 * Home page
 */
app.get('/', (req: Request, res: Response) => {
  console.log('[GET /] Home page – user logged in:', !!currentUserTokens)
  if (currentUserTokens) {
    res.send(`
      <!DOCTYPE html>
      <html>
      <head>
        <title>Sample OAuth Client - Logged In</title>
        <style>
          body { font-family: Arial, sans-serif; max-width: 600px; margin: 50px auto; padding: 20px; }
          .card { background: #f5f5f5; padding: 20px; border-radius: 8px; margin: 20px 0; }
          .token { word-break: break-all; font-family: monospace; font-size: 12px; background: #fff; padding: 10px; margin: 10px 0; border-radius: 4px; }
          button { background: #007bff; color: white; border: none; padding: 10px 20px; border-radius: 4px; cursor: pointer; margin: 5px; }
          button.danger { background: #dc3545; }
          button:hover { opacity: 0.9; }
        </style>
      </head>
      <body>
        <h1>Logged In!</h1>
        <div class="card">
          <h3>Access Token:</h3>
          <div class="token">${currentUserTokens.access_token}</div>
          <h3>Token Type:</h3>
          <p>${currentUserTokens.token_type}</p>
          <h3>Expires In:</h3>
          <p>${currentUserTokens.expires_in} seconds</p>
          <h3>Scopes:</h3>
          <p>${currentUserTokens.scope}</p>
          ${currentUserTokens.refresh_token ? `
          <h3>Refresh Token:</h3>
          <div class="token">${currentUserTokens.refresh_token}</div>
          ` : ''}
        </div>
        <div>
          <a href="/api/org"><button>Test API: Get Organization</button></a>
          <a href="/api/userinfo"><button>Test API: Get User Info</button></a>
          <a href="/scope-tests"><button>Scope Tests (Org / Users / Teams / User Groups)</button></a>
          <a href="/logout"><button class="danger">Logout</button></a>
        </div>
        <br><br>
        <a href="/admin" style="color: #6c757d; font-size: 14px;">Admin / Cleanup</a>
      </body>
      </html>
    `)
  } else {
    res.send(`
      <!DOCTYPE html>
      <html>
      <head>
        <title>Sample OAuth Client</title>
        <style>
          body { font-family: Arial, sans-serif; max-width: 600px; margin: 50px auto; padding: 20px; text-align: center; }
          button { background: #007bff; color: white; border: none; padding: 15px 30px; border-radius: 4px; cursor: pointer; font-size: 16px; }
          button:hover { opacity: 0.9; }
          .info { background: #f5f5f5; padding: 20px; border-radius: 8px; margin: 20px 0; text-align: left; }
          code { background: #e9e9e9; padding: 2px 6px; border-radius: 3px; }
        </style>
      </head>
      <body>
        <h1>Sample OAuth Client</h1>
        <p>This demonstrates the OAuth 2.0 Authorization Code flow with PipesHub.</p>
        <a href="/login"><button>Login with PipesHub</button></a>
        <div class="info">
          <h3>How it works:</h3>
          <ol>
            <li>Click "Login with PipesHub"</li>
            <li>You'll be redirected to PipesHub</li>
            <li>Log in (if not already)</li>
            <li>Approve the permissions</li>
            <li>You'll be redirected back here with your tokens</li>
          </ol>
          <h3>Configuration:</h3>
          <p>Backend: <code>${config.backend.url}</code></p>
          <p>Client ID: <code>${config.oauth.clientId}</code></p>
          <p>Scopes: <code>${config.oauth.scopes}</code></p>
        </div>
        <br>
        <a href="/admin" style="color: #6c757d; font-size: 14px;">Admin / Cleanup</a>
      </body>
      </html>
    `)
  }
})

/**
 * Initiate OAuth login flow
 */
app.get('/login', (req: Request, res: Response) => {
  const codeVerifier = generateCodeVerifier()
  const codeChallenge = generateCodeChallenge(codeVerifier)
  const state = generateState()

  pendingAuthorizations.set(state, {
    codeVerifier,
    timestamp: Date.now(),
  })

  console.log('[GET /login] Starting OAuth flow – scopes requested:', config.oauth.scopes)

  const authUrl = new URL('/api/v1/oauth2/authorize', config.backend.url)
  authUrl.searchParams.set('client_id', config.oauth.clientId)
  authUrl.searchParams.set('redirect_uri', config.oauth.callbackUrl)
  authUrl.searchParams.set('response_type', 'code')
  authUrl.searchParams.set('scope', config.oauth.scopes)
  authUrl.searchParams.set('state', state)
  authUrl.searchParams.set('code_challenge', codeChallenge)
  authUrl.searchParams.set('code_challenge_method', 'S256')

  console.log('[GET /login] Redirecting to:', authUrl.toString())
  res.redirect(authUrl.toString())
})

/**
 * OAuth callback handler
 */
app.get('/callback', async (req: Request, res: Response) => {
  const { code, state, error, error_description } = req.query
  console.log('[GET /callback] OAuth callback – error?', error || 'none', 'code present?', !!code)

  if (error) {
    return res.send(`
      <!DOCTYPE html>
      <html>
      <head><title>OAuth Error</title></head>
      <body>
        <h1>Authorization Failed</h1>
        <p>Error: ${escapeHtml(error as string)}</p>
        <p>Description: ${escapeHtml(error_description as string) || 'No description provided'}</p>
        <a href="/">Go Back</a>
      </body>
      </html>
    `)
  }

  const pending = pendingAuthorizations.get(state as string)
  if (!pending) {
    console.log('[GET /callback] Invalid state – possible CSRF or expired session')
    return res.status(400).send('Invalid state parameter. Possible CSRF attack.')
  }
  pendingAuthorizations.delete(state as string)

  try {
    console.log('[GET /callback] Exchanging authorization code for tokens at', config.backend.url + '/api/v1/oauth2/token')

    const tokenUrl = new URL('/api/v1/oauth2/token', config.backend.url)
    const tokenBody = new URLSearchParams({
      grant_type: 'authorization_code',
      code: code as string,
      redirect_uri: config.oauth.callbackUrl,
      client_id: config.oauth.clientId,
      client_secret: config.oauth.clientSecret,
      code_verifier: pending.codeVerifier,
    }).toString()

    const response = await makeRequest<TokenResponse>(tokenUrl.toString(), {
      method: 'POST',
      headers: {
        'Content-Type': 'application/x-www-form-urlencoded',
      },
      body: tokenBody,
    })

    if (response.status !== 200) {
      const errorData = response.data as OAuthTokenError
      throw new Error(errorData.error_description || errorData.error || 'Token exchange failed')
    }

    currentUserTokens = response.data
    console.log('[GET /callback] Tokens received – scopes:', currentUserTokens.scope)
    res.redirect('/')
  } catch (err) {
    console.error('[GET /callback] Token exchange failed:', (err as Error).message)
    res.send(`
      <!DOCTYPE html>
      <html>
      <head><title>Token Exchange Error</title></head>
      <body>
        <h1>Token Exchange Failed</h1>
        <p>${escapeHtml((err as Error).message)}</p>
        <a href="/">Go Back</a>
      </body>
      </html>
    `)
  }
})

/**
 * Test API: Get organization info
 */
app.get('/api/org', async (req: Request, res: Response) => {
  console.log('[GET /api/org] Request – has token?', !!currentUserTokens)
  if (!currentUserTokens) {
    return res.redirect('/')
  }

  try {
    const response = await makeRequest(`${config.backend.url}/api/v1/org`, {
      headers: {
        'Authorization': `Bearer ${currentUserTokens.access_token}`,
      },
    })

    res.send(`
      <!DOCTYPE html>
      <html>
      <head>
        <title>Organization Info</title>
        <style>
          body { font-family: Arial, sans-serif; max-width: 800px; margin: 50px auto; padding: 20px; }
          pre { background: #f5f5f5; padding: 20px; border-radius: 8px; overflow: auto; }
        </style>
      </head>
      <body>
        <h1>Organization Info (via OAuth)</h1>
        <p>Status: ${response.status}</p>
        <pre>${JSON.stringify(response.data, null, 2)}</pre>
        <a href="/">Back</a>
      </body>
      </html>
    `)
  } catch (err) {
    console.log('[GET /api/org] Error:', (err as Error).message)
    res.send(`Error: ${escapeHtml((err as Error).message)}`)
  }
})

/**
 * Test API: Get user info
 */
app.get('/api/userinfo', async (req: Request, res: Response) => {
  console.log('[GET /api/userinfo] Request – has token?', !!currentUserTokens)
  if (!currentUserTokens) {
    return res.redirect('/')
  }

  try {
    const response = await makeRequest(`${config.backend.url}/api/v1/oauth2/userinfo`, {
      headers: {
        'Authorization': `Bearer ${currentUserTokens.access_token}`,
      },
    })

    res.send(`
      <!DOCTYPE html>
      <html>
      <head>
        <title>User Info</title>
        <style>
          body { font-family: Arial, sans-serif; max-width: 800px; margin: 50px auto; padding: 20px; }
          pre { background: #f5f5f5; padding: 20px; border-radius: 8px; overflow: auto; }
        </style>
      </head>
      <body>
        <h1>User Info (OIDC /userinfo)</h1>
        <p>Status: ${response.status}</p>
        <pre>${JSON.stringify(response.data, null, 2)}</pre>
        <a href="/">Back</a>
      </body>
      </html>
    `)
  } catch (err) {
    console.log('[GET /api/userinfo] Error:', (err as Error).message)
    res.send(`Error: ${escapeHtml((err as Error).message)}`)
  }
})

/**
 * Logout
 */
app.get('/logout', (req: Request, res: Response) => {
  console.log('[GET /logout] Clearing tokens, redirecting to home')
  currentUserTokens = null
  res.redirect('/')
})

/**
 * Scope tests: call Org, Users, User Groups, Teams APIs with current token.
 * When token has required scope → expect 2xx (or 4xx if body/params missing).
 * When token does NOT have scope → expect 403.
 */
app.get('/scope-tests', async (req: Request, res: Response) => {
  console.log('[GET /scope-tests] Scope tests requested – has token?', !!currentUserTokens)
  if (!currentUserTokens) {
    return res.redirect('/')
  }

  const tokenScopes = parseScopes(currentUserTokens.scope)
  console.log('[GET /scope-tests] Token scopes:', tokenScopes.join(', ') || '(none)')
  const results: ScopeTestResult[] = await runScopeTests(
    config.backend.url,
    currentUserTokens.access_token,
    tokenScopes,
  )

  const passedCount = results.filter((r) => r.passed).length
  const totalCount = results.length
  console.log('[GET /scope-tests] Done –', passedCount, '/', totalCount, 'tests passed')

  const rows = results
    .map(
      (r) => `
    <tr>
      <td>${escapeHtml(r.case.category)}</td>
      <td>${escapeHtml(r.case.name)}</td>
      <td><code>${escapeHtml(r.case.method)} ${escapeHtml(r.case.path)}</code></td>
      <td><code>${escapeHtml(r.case.requiredScope)}</code></td>
      <td>${tokenScopes.includes(r.case.requiredScope) ? 'Yes' : 'No'}</td>
      <td>${r.status >= 0 ? r.status : '—'}</td>
      <td style="color: ${r.passed ? '#28a745' : '#dc3545'}">${r.passed ? '✓ Pass' : '✗ Fail'}</td>
      <td>${escapeHtml(r.message)}</td>
    </tr>`,
    )
    .join('')

  res.send(`
    <!DOCTYPE html>
    <html>
    <head>
      <title>Scope Tests - Org / Users / Teams / KB / Search / Conversations / Agents / Connectors</title>
      <style>
        body { font-family: Arial, sans-serif; max-width: 1000px; margin: 50px auto; padding: 20px; }
        table { border-collapse: collapse; width: 100%; margin: 20px 0; font-size: 14px; }
        th, td { border: 1px solid #ddd; padding: 8px 12px; text-align: left; }
        th { background: #f5f5f5; }
        code { background: #e9e9e9; padding: 2px 6px; border-radius: 3px; font-size: 12px; }
        .summary { background: #f5f5f5; padding: 15px; border-radius: 8px; margin-bottom: 20px; }
        .info { background: #d1ecf1; border: 1px solid #bee5eb; padding: 15px; border-radius: 4px; margin: 15px 0; font-size: 14px; }
        a { color: #007bff; }
      </style>
    </head>
    <body>
      <h1>Scope Tests (Org / Users / Teams / User Groups / KB / Search / Conversations / Agents / Connectors)</h1>
      <div class="summary">
        <strong>Result:</strong> ${passedCount} / ${totalCount} tests passed.
        <br><strong>Token scopes:</strong> <code>${escapeHtml(currentUserTokens.scope || 'none')}</code>
      </div>
      <div class="info">
        <strong>How to interpret:</strong> For each endpoint, if your token has the required scope, the API should return 2xx (or 4xx if the request is invalid). If your token does <em>not</em> have the scope, the API should return <strong>403</strong>. Use different <code>SCOPES</code> when logging in to test both cases.
      </div>
      <table>
        <thead>
          <tr>
            <th>Category</th>
            <th>Test</th>
            <th>Endpoint</th>
            <th>Required scope</th>
            <th>Has scope?</th>
            <th>Status</th>
            <th>Result</th>
            <th>Message</th>
          </tr>
        </thead>
        <tbody>${rows}</tbody>
      </table>
      <p><a href="/">← Back to Home</a></p>
    </body>
    </html>
  `)
})

/**
 * Admin/Cleanup page
 */
app.get('/admin', (req: Request, res: Response) => {
  res.send(`
    <!DOCTYPE html>
    <html>
    <head>
      <title>Sample OAuth Client - Admin</title>
      <style>
        body { font-family: Arial, sans-serif; max-width: 600px; margin: 50px auto; padding: 20px; }
        .card { background: #f5f5f5; padding: 20px; border-radius: 8px; margin: 20px 0; }
        button { padding: 10px 20px; border-radius: 4px; cursor: pointer; margin: 5px; border: none; color: white; }
        button.danger { background: #dc3545; }
        button.warning { background: #ffc107; color: black; }
        button:hover { opacity: 0.9; }
        input[type="password"] { width: 100%; padding: 10px; margin: 10px 0; border: 1px solid #ddd; border-radius: 4px; box-sizing: border-box; }
        .warning-box { background: #fff3cd; border: 1px solid #ffc107; padding: 15px; border-radius: 4px; margin: 15px 0; }
        .info-box { background: #d1ecf1; border: 1px solid #bee5eb; padding: 15px; border-radius: 4px; margin: 15px 0; }
        code { background: #e9e9e9; padding: 2px 6px; border-radius: 3px; word-break: break-all; }
      </style>
    </head>
    <body>
      <h1>Admin / Cleanup</h1>
      <div class="info-box">
        <strong>Current Configuration:</strong><br>
        Client ID: <code>${config.oauth.clientId}</code><br>
        Backend URL: <code>${config.backend.url}</code><br>
        Admin Token: <code>${config.admin.token ? 'Configured' : 'Not configured'}</code>
      </div>
      <div class="card">
        <h3>Delete OAuth Application</h3>
        <p>This will permanently delete the OAuth application from PipesHub.</p>
        <form action="/admin/delete-app" method="POST">
          <label for="token">Admin JWT Token:</label>
          <input type="password" id="token" name="token" placeholder="Paste your admin JWT token here" value="${config.admin.token || ''}" required>
          <div class="warning-box">
            <strong>Warning:</strong> This action cannot be undone.
          </div>
          <button type="submit" class="danger">Delete OAuth App</button>
        </form>
      </div>
      <div class="card">
        <h3>Stop Sample Server</h3>
        <p>This will stop the sample OAuth client server.</p>
        <form action="/admin/shutdown" method="POST">
          <button type="submit" class="warning">Stop Server</button>
        </form>
      </div>
      <div class="card">
        <h3>Full Cleanup</h3>
        <p>Delete the OAuth app AND stop the server.</p>
        <form action="/admin/full-cleanup" method="POST">
          <label for="token2">Admin JWT Token:</label>
          <input type="password" id="token2" name="token" placeholder="Paste your admin JWT token here" value="${config.admin.token || ''}" required>
          <button type="submit" class="danger">Full Cleanup</button>
        </form>
      </div>
      <br>
      <a href="/">← Back to Home</a>
    </body>
    </html>
  `)
})

/**
 * Get OAuth app ID by client ID
 */
async function getAppIdByClientId(clientId: string, token: string): Promise<string> {
  const response = await makeRequest<OAuthAppsResponse | OAuthApp[]>(
    `${config.backend.url}/api/v1/oauth-clients`,
    {
      headers: {
        Authorization: `Bearer ${token}`,
      },
    }
  )

  if (response.status !== 200) {
    throw new Error(`Failed to list apps: ${JSON.stringify(response.data)}`)
  }

  const apps: OAuthApp[] = Array.isArray(response.data)
    ? response.data
    : (response.data.data || response.data.apps || [])

  if (!Array.isArray(apps)) {
    throw new Error(`Unexpected response format: ${JSON.stringify(response.data)}`)
  }

  const app = apps.find((a: OAuthApp) => a.clientId === clientId)
  if (!app) {
    throw new Error(`OAuth app with clientId ${clientId} not found`)
  }

  return app.id || app._id || ''
}

/**
 * Delete OAuth application
 */
async function deleteOAuthApp(appId: string, token: string): Promise<boolean> {
  const response = await makeRequest(`${config.backend.url}/api/v1/oauth-clients/${appId}`, {
    method: 'DELETE',
    headers: {
      Authorization: `Bearer ${token}`,
    },
  })

  if (response.status !== 200 && response.status !== 204) {
    throw new Error(`Failed to delete app: ${JSON.stringify(response.data)}`)
  }

  return true
}

/**
 * Delete OAuth App endpoint
 */
app.post('/admin/delete-app', rateLimit, async (req: Request, res: Response) => {
  const token: string = req.body.token || config.admin.token

  if (!token) {
    return res.status(400).send(`
      <!DOCTYPE html>
      <html>
      <head><title>Error</title></head>
      <body>
        <h1>Error</h1>
        <p>Admin JWT token is required</p>
        <a href="/admin">← Back</a>
      </body>
      </html>
    `)
  }

  try {
    console.log('Deleting OAuth app...')
    const appId = await getAppIdByClientId(config.oauth.clientId, token)
    console.log('Found app ID:', appId)

    await deleteOAuthApp(appId, token)
    console.log('OAuth app deleted successfully')

    res.send(`
      <!DOCTYPE html>
      <html>
      <head><title>Success</title></head>
      <body style="font-family: Arial, sans-serif; max-width: 600px; margin: 50px auto; padding: 20px; text-align: center;">
        <h1 style="color: #28a745;">OAuth App Deleted!</h1>
        <p>The OAuth application has been successfully deleted from PipesHub.</p>
        <p>Client ID: <code>${config.oauth.clientId}</code></p>
        <br>
        <p>You can now stop the server or <a href="/admin">go back to admin</a>.</p>
      </body>
      </html>
    `)
  } catch (err) {
    console.error('Failed to delete OAuth app:', (err as Error).message)
    res.status(500).send(`
      <!DOCTYPE html>
      <html>
      <head><title>Error</title></head>
      <body style="font-family: Arial, sans-serif; max-width: 600px; margin: 50px auto; padding: 20px;">
        <h1 style="color: #dc3545;">Failed to Delete OAuth App</h1>
        <p>${escapeHtml((err as Error).message)}</p>
        <a href="/admin">← Back to Admin</a>
      </body>
      </html>
    `)
  }
})

/**
 * Shutdown server endpoint
 */
app.post('/admin/shutdown', rateLimit, (req: Request, res: Response) => {
  res.send(`
    <!DOCTYPE html>
    <html>
    <head><title>Server Stopping</title></head>
    <body style="font-family: Arial, sans-serif; max-width: 600px; margin: 50px auto; padding: 20px; text-align: center;">
      <h1>Server Stopping...</h1>
      <p>The sample OAuth client server is shutting down.</p>
      <p>You can close this window.</p>
    </body>
    </html>
  `)

  console.log('Shutdown requested, stopping server...')
  setTimeout(() => {
    if (server) {
      server.close(() => {
        console.log('Server stopped')
        process.exit(0)
      })
    } else {
      process.exit(0)
    }
  }, 500)
})

/**
 * Full cleanup
 */
app.post('/admin/full-cleanup', rateLimit, async (req: Request, res: Response) => {
  const token: string = req.body.token || config.admin.token

  if (!token) {
    return res.status(400).send(`
      <!DOCTYPE html>
      <html>
      <head><title>Error</title></head>
      <body>
        <h1>Error</h1>
        <p>Admin JWT token is required</p>
        <a href="/admin">← Back</a>
      </body>
      </html>
    `)
  }

  try {
    console.log('Full cleanup: Deleting OAuth app...')
    const appId = await getAppIdByClientId(config.oauth.clientId, token)
    await deleteOAuthApp(appId, token)
    console.log('OAuth app deleted successfully')

    res.send(`
      <!DOCTYPE html>
      <html>
      <head><title>Cleanup Complete</title></head>
      <body style="font-family: Arial, sans-serif; max-width: 600px; margin: 50px auto; padding: 20px; text-align: center;">
        <h1 style="color: #28a745;">Cleanup Complete!</h1>
        <p>OAuth application deleted and server is stopping.</p>
        <p>You can close this window.</p>
      </body>
      </html>
    `)

    console.log('Shutdown requested, stopping server...')
    setTimeout(() => {
      if (server) {
        server.close(() => {
          console.log('Server stopped')
          process.exit(0)
        })
      } else {
        process.exit(0)
      }
    }, 500)
  } catch (err) {
    console.error('Cleanup failed:', (err as Error).message)
    res.status(500).send(`
      <!DOCTYPE html>
      <html>
      <head><title>Error</title></head>
      <body style="font-family: Arial, sans-serif; max-width: 600px; margin: 50px auto; padding: 20px;">
        <h1 style="color: #dc3545;">Cleanup Failed</h1>
        <p>${escapeHtml((err as Error).message)}</p>
        <a href="/admin">← Back to Admin</a>
      </body>
      </html>
    `)
  }
})

// Start server
server = app.listen(config.server.port, () => {
  console.log(`Sample OAuth Client running at http://localhost:${config.server.port}`)
  console.log('')
  console.log('Steps to test:')
  console.log('1. Make sure PipesHub backend is running on', config.backend.url)
  console.log('2. Make sure PipesHub frontend is running on http://localhost:3001')
  console.log('3. Open http://localhost:' + config.server.port + ' in your browser')
  console.log('4. Click "Login with PipesHub"')
  console.log('')
})
