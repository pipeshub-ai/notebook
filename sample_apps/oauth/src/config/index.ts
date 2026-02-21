/**
 * Application configuration
 */

export interface AppConfig {
    backend: {
        url: string
    }
    oauth: {
        clientId: string
        clientSecret: string
        callbackUrl: string
        scopes: string
    }
    server: {
        port: number
    }
    rateLimit: {
        windowMs: number
        maxRequests: number
    }
    admin: {
        token: string | null
    }
}

/**
 * Load and validate application configuration from environment
 */
export function loadConfig(): AppConfig {
    const port = parseInt(process.env.PORT || '8888', 10)
    const backendUrl = process.env.BACKEND_URL || 'http://localhost:3000'

    const defaultScopes = 'openid profile email offline_access'
    const config: AppConfig = {
        backend: {
            url: backendUrl,
        },
        oauth: {
            clientId: process.env.CLIENT_ID || '',
            clientSecret: process.env.CLIENT_SECRET || '',
            callbackUrl: `http://localhost:${port}/callback`,
            scopes: process.env.SCOPES || defaultScopes,
        },
        server: {
            port,
        },
        rateLimit: {
            windowMs: 60000, // 1 minute
            maxRequests: 5,
        },
        admin: {
            token: process.env.ADMIN_JWT_TOKEN || null,
        },
    }

    return config
}

/**
 * Validate required configuration
 */
export function validateConfig(config: AppConfig): void {
    if (!config.oauth.clientId || !config.oauth.clientSecret) {
        console.error('Error: CLIENT_ID and CLIENT_SECRET environment variables are required')
        console.error('Usage: CLIENT_ID=xxx CLIENT_SECRET=xxx npm start')
        console.error('')
        console.error('To create an OAuth app, run:')
        console.error('  ADMIN_JWT_TOKEN=xxx npm run create-app')
        process.exit(1)
    }
}
