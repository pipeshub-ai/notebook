# PipesHub OAuth Sample Client

A sample application demonstrating the OAuth 2.0 Authorization Code flow with PKCE for PipesHub.

## Overview

This sample client shows how to integrate OAuth authentication with PipesHub. It implements:

- OAuth 2.0 Authorization Code flow
- PKCE (Proof Key for Code Exchange) for enhanced security
- Token exchange and storage
- API calls using access tokens
- Token refresh flow

## Prerequisites

- Node.js (v14 or higher)
- PipesHub backend running on `http://localhost:3000`
- PipesHub frontend running on `http://localhost:3001`
- Admin JWT token (for creating the OAuth app)

## Quick Start

### 1. Install Dependencies

```bash
npm install
```

### 2. Create an OAuth Application

You need an admin JWT token from PipesHub to create the OAuth app:

```bash
ADMIN_JWT_TOKEN=your_jwt_token npm run create-app
```

This will:
- Register a new OAuth application with PipesHub
- Save the `CLIENT_ID` and `CLIENT_SECRET` to a `.env` file

### 3. Start the Sample Client

```bash
npm start
```

The client will run at `http://localhost:8888`.

### 4. Test the Flow

1. Open `http://localhost:8888` in your browser
2. Click "Login with PipesHub"
3. Log in to PipesHub (if not already logged in)
4. Approve the requested permissions
5. You'll be redirected back with your access token

## Configuration

Configuration can be set via environment variables or a `.env` file:

| Variable | Description | Default |
|----------|-------------|---------|
| `CLIENT_ID` | OAuth client ID | Required |
| `CLIENT_SECRET` | OAuth client secret | Required |
| `BACKEND_URL` | PipesHub backend URL | `http://localhost:3000` |
| `PORT` | Sample client port | `8888` |
| `ADMIN_JWT_TOKEN` | Admin token for cleanup | Optional |

## Available Scripts

| Script | Command | Description |
|--------|---------|-------------|
| Start server | `npm start` | Run the sample OAuth client |
| Create app | `npm run create-app` | Create OAuth app in PipesHub |
| Cleanup | `npm run cleanup` | Delete OAuth app and stop server |
| Stop server | `npm run stop` | Stop the server only |
| Delete app | `npm run delete-app` | Delete the OAuth app |

## OAuth Flow

```
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│                 │     │                 │     │                 │
│   User/Browser  │     │  Sample Client  │     │    PipesHub     │
│                 │     │  (port 8888)    │     │  (port 3000)    │
└────────┬────────┘     └────────┬────────┘     └────────┬────────┘
         │                       │                       │
         │  1. Click Login       │                       │
         │──────────────────────>│                       │
         │                       │                       │
         │  2. Redirect to       │                       │
         │     /authorize        │                       │
         │<──────────────────────│                       │
         │                       │                       │
         │  3. Authorization request with PKCE           │
         │──────────────────────────────────────────────>│
         │                       │                       │
         │  4. User logs in and approves                 │
         │<──────────────────────────────────────────────│
         │                       │                       │
         │  5. Redirect to callback with code            │
         │──────────────────────>│                       │
         │                       │                       │
         │                       │  6. Exchange code     │
         │                       │     for tokens        │
         │                       │──────────────────────>│
         │                       │                       │
         │                       │  7. Access + Refresh  │
         │                       │     tokens            │
         │                       │<──────────────────────│
         │                       │                       │
         │  8. Show tokens       │                       │
         │<──────────────────────│                       │
         │                       │                       │
```

## Requested Scopes

The sample client requests the following scopes:

- `org:read` - Read organization information
- `user:read` - Read user information
- `openid` - OpenID Connect
- `profile` - User profile
- `email` - User email
- `offline_access` - Refresh tokens

## API Endpoints (Sample Client)

| Endpoint | Description |
|----------|-------------|
| `GET /` | Home page with login button or token display |
| `GET /login` | Initiates OAuth flow |
| `GET /callback` | OAuth callback handler |
| `GET /logout` | Clears tokens |
| `GET /api/org` | Test API: Get organization info |
| `GET /api/userinfo` | Test API: Get user info |
| `GET /admin` | Admin panel for cleanup |

## Cleanup

### Via Web Interface

1. Navigate to `http://localhost:8888/admin`
2. Enter your admin JWT token
3. Click "Delete OAuth App" or "Full Cleanup"

### Via Command Line

```bash
# Delete app and stop server
ADMIN_JWT_TOKEN=your_token CLIENT_ID=your_client_id npm run cleanup

# Just stop the server
npm run stop
```

## Security Notes

- This is a **sample application** for demonstration purposes
- In production, never store tokens in memory or expose secrets in URLs
- Use secure session management and proper token storage
- The `.env` file containing secrets should never be committed to version control
- PKCE is used to protect against authorization code interception attacks

## Troubleshooting

### Connection Refused

Make sure the PipesHub backend is running:
```
Error: Connection refused to http://localhost:3000
```

### Invalid Client

Check that `CLIENT_ID` and `CLIENT_SECRET` match the registered OAuth app:
```
Error: invalid_client
```

### Invalid State

The state parameter didn't match. This could indicate a CSRF attack or an expired session. Try logging in again.

## License

MIT
