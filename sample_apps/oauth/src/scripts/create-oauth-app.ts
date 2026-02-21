/**
 * Script to create an OAuth application in PipesHub
 *
 * Prerequisites:
 * 1. Backend server running on http://localhost:3000
 * 2. An admin user JWT token (set as ADMIN_JWT_TOKEN environment variable)
 *
 * Usage:
 *   ADMIN_JWT_TOKEN=your_jwt_token npm run create-app
 */

import fs from 'fs'
import path from 'path'
import type { OAuthAppConfig, CreateOAuthAppResult, OAuthAppResponse } from '../types'
import { makeRequest, maskSecret, loadEnvFile } from '../utils'

loadEnvFile()

// Configuration
const BACKEND_URL: string = process.env.BACKEND_URL || 'http://localhost:3000'
const ADMIN_JWT_TOKEN: string | undefined = process.env.ADMIN_JWT_TOKEN

if (!ADMIN_JWT_TOKEN) {
    console.error('Error: ADMIN_JWT_TOKEN environment variable is required')
    console.error('Usage: ADMIN_JWT_TOKEN=your_jwt_token npm run create-app')
    process.exit(1)
}

// OAuth app configuration – allow all scopes used by scope tests (Org, Users, User Groups, Teams)
const oauthAppConfig: OAuthAppConfig = {
    name: 'Sample OAuth Client',
    description: 'A sample application demonstrating PipesHub OAuth flow',
    redirectUris: ['http://localhost:8888/callback'],
    allowedGrantTypes: ['authorization_code', 'refresh_token'],
    allowedScopes: [
        'usergroup:read', 'usergroup:write',
        'team:read', 'team:write',
        'openid', 'profile', 'email', 'offline_access',
    ],
    isConfidential: true,
    accessTokenLifetime: 3600,
    refreshTokenLifetime: 2592000,
}

async function createOAuthApp(): Promise<CreateOAuthAppResult> {
    console.log('Creating OAuth application...')
    console.log('Backend URL:', BACKEND_URL)

    const url = `${BACKEND_URL}/api/v1/oauth-clients`
    const response = await makeRequest<CreateOAuthAppResult>(url, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'Authorization': `Bearer ${ADMIN_JWT_TOKEN}`,
        },
        body: JSON.stringify(oauthAppConfig),
    })

    if (response.status < 200 || response.status >= 300) {
        throw new Error(`HTTP ${response.status}: ${JSON.stringify(response.data)}`)
    }

    return response.data
}

async function main(): Promise<void> {
    try {
        const result: CreateOAuthAppResult = await createOAuthApp()

        // Extract app data (handle both { app: {...} } and direct { clientId, ... } formats)
        const app: OAuthAppResponse = (result.app || result) as OAuthAppResponse

        console.log('\n========================================')
        console.log('OAuth Application Created Successfully!')
        console.log('========================================\n')
        console.log('Client ID:', app.clientId)
        console.log('Client Secret:', maskSecret(app.clientSecret), '(full secret saved to .env)')
        console.log('')

        // Save credentials to .env file
        const envContent: string = `# OAuth Client Credentials - Generated ${new Date().toISOString()}
CLIENT_ID=${app.clientId}
CLIENT_SECRET=${app.clientSecret}
BACKEND_URL=http://localhost:3000
`
        const envPath: string = path.join(process.cwd(), '.env')
        fs.writeFileSync(envPath, envContent)
        console.log('Credentials saved to:', envPath)
        console.log('\nTo run the sample client:')
        console.log('  npm start')
        console.log('\n(Credentials will be loaded from .env file)')
    } catch (error) {
        console.error('Failed to create OAuth app:', (error as Error).message)
        process.exit(1)
    }
}

main()
