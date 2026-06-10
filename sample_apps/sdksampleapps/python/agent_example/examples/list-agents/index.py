"""
List Agents Example
===================

This example fetches and prints all agents for the authenticated user by
calling the PipesHub API GET /agents endpoint.

Authentication is handled in the same way as the auth example:

1. Static Bearer Token
   If the environment variable `PIPESHUB_BEARER_AUTH` is set, that token
   is used directly for the Authorization header.

2. OAuth 2.0 Authorization Code Flow with PKCE
   If no bearer token is set, the script uses OAuth with a browser and
   local callback server to obtain an access token.

The API response is normalized to a list: whether the API returns a raw
list of agents or a wrapper object (e.g. `{"data": [...]}`), callers
receive a consistent list so that downstream code does not need to
handle multiple response shapes.

Typical usage:

    python examples/list-agents/index.py
    python main.py list-agents
"""

import base64
import hashlib
import os
import secrets
import sys
import threading
import time
import webbrowser
from http.server import BaseHTTPRequestHandler, HTTPServer
from typing import Any, Dict, Optional
from urllib.parse import parse_qs, urlencode, urlparse

import requests
from dotenv import load_dotenv

# -------------------------------------------------------------------------
# Project Path Setup
# -------------------------------------------------------------------------
# This ensures that running this script directly still allows imports from
# the project source directory (e.g. `src.logger`).
# Without this adjustment, Python would not resolve the import correctly.
# -------------------------------------------------------------------------

_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, _root)

from src.logger import logger

load_dotenv()

# -------------------------------------------------------------------------
# Configuration
# -------------------------------------------------------------------------
# Override with environment variables: PIPESHUB_SERVER_URL,
# PIPESHUB_OAUTH_REDIRECT_PORT.
# -------------------------------------------------------------------------

# Base URL of the PipesHub API (no trailing slash).
DEFAULT_SERVER_URL = "https://app.pipeshub.com/api/v1"

# OAuth scopes requested during authentication.
DEFAULT_OAUTH_SCOPES = "openid profile email offline_access"

# Local port used to receive OAuth redirect callback.
# Must match the redirect URI configured in the PipesHub OAuth application.
DEFAULT_OAUTH_REDIRECT_PORT = 8765

# OAuth callback endpoint path.
OAUTH_CALLBACK_PATH = "/callback"


# -------------------------------------------------------------------------
# PKCE Helpers
# -------------------------------------------------------------------------
# PipesHub OAuth requires PKCE (Proof Key for Code Exchange).
# PKCE protects the authorization code flow by binding the authorization
# request and token request using a cryptographically random secret.
# -------------------------------------------------------------------------


def _pkce_code_verifier() -> str:
    """
    Generate a PKCE code verifier.

    The verifier is a high-entropy random string that will later be sent to
    the token endpoint. The server validates it against the challenge that
    was sent during the authorization request.

    Returns
    -------
    str
        A URL-safe random string suitable for PKCE verification.
    """
    return secrets.token_urlsafe(43)


def _pkce_code_challenge(verifier: str) -> str:
    """
    Generate a PKCE code challenge from a verifier.

    The challenge is derived by hashing the verifier with SHA-256 and
    encoding it with base64url.

    Parameters
    ----------
    verifier : str
        PKCE verifier previously generated.

    Returns
    -------
    str
        Encoded challenge sent in the OAuth authorize request.
    """
    digest = hashlib.sha256(verifier.encode("utf-8")).digest()
    return base64.urlsafe_b64encode(digest).decode("utf-8").rstrip("=")


# -------------------------------------------------------------------------
# OAuth Browser Flow
# -------------------------------------------------------------------------
# This implements the OAuth 2.0 Authorization Code Flow with PKCE.
#
# Steps:
# 1. Open the browser with the PipesHub authorization URL
# 2. Run a local HTTP server waiting for the redirect callback
# 3. Extract the authorization code
# 4. Exchange the code for an access token
# -------------------------------------------------------------------------


def _oauth_flow_browser(server_url: str, client_id: str, client_secret: str, redirect_port: int) -> str:
    """
    Execute OAuth login using a browser and local callback server.

    This flow is intended for developer tools and CLI utilities where the
    user can interact with a browser.

    Parameters
    ----------
    server_url : str
        Base URL of the PipesHub API.

    client_id : str
        OAuth client ID registered with PipesHub.

    client_secret : str
        OAuth client secret.

    redirect_port : int
        Local port used for the OAuth redirect callback.

    Returns
    -------
    str
        Access token to be used as a Bearer token in API requests.

    Raises
    ------
    RuntimeError
        If the user denies authorization, the callback is missing the code,
        state does not match, token exchange fails, or the response lacks
        an access token.
    """
    base = server_url.rstrip("/")
    authorize_url = f"{base}/oauth2/authorize"
    token_url = f"{base}/oauth2/token"
    redirect_uri = f"http://localhost:{redirect_port}{OAUTH_CALLBACK_PATH}"

    # -----------------------------------------------------------------
    # OAuth state protects against CSRF attacks.
    # PKCE values protect the authorization code exchange.
    # -----------------------------------------------------------------

    state = secrets.token_urlsafe(32)
    code_verifier = _pkce_code_verifier()
    code_challenge = _pkce_code_challenge(code_verifier)

    auth_result: Dict[str, Optional[str]] = {"code": None, "state": None, "error": None}

    class CallbackHandler(BaseHTTPRequestHandler):
        """
        Minimal HTTP handler used only once.

        PipesHub redirects the browser to:
            http://localhost:<port>/callback?code=...&state=...

        This handler extracts the authorization code and stores it in
        the shared `auth_result` dictionary.
        """

        def do_GET(self) -> None:
            parsed = urlparse(self.path)
            if parsed.path != OAUTH_CALLBACK_PATH:
                self._send(400, "Not found")
                return
            q = parse_qs(parsed.query)
            if "error" in q:
                auth_result["error"] = q["error"][0]
                self._send(200, "Login failed. You can close this tab.")
                return
            if "code" not in q:
                self._send(400, "Missing code")
                return
            auth_result["code"] = q["code"][0]
            auth_result["state"] = (q.get("state") or [None])[0]
            self._send(200, "Login successful! You can close this tab.")

        def _send(self, code: int, body: str) -> None:
            self.send_response(code)
            self.send_header("Content-type", "text/html; charset=utf-8")
            self.end_headers()
            self.wfile.write(f"<h1>{body}</h1>".encode("utf-8"))

        def log_message(self, format: str, *args: Any) -> None:
            # Disable default HTTP server logging.
            pass

    # Start callback listener so we can receive the OAuth redirect.
    server = HTTPServer(("localhost", redirect_port), CallbackHandler)

    thread = threading.Thread(target=server.handle_request)
    thread.daemon = True
    thread.start()

    params = {
        "client_id": client_id,
        "redirect_uri": redirect_uri,
        "response_type": "code",
        "scope": DEFAULT_OAUTH_SCOPES,
        "state": state,
        "code_challenge": code_challenge,
        "code_challenge_method": "S256",
    }
    login_url = f"{authorize_url}?{urlencode(params)}"

    try:
        logger.info("Opening browser for PipesHub login...")
        webbrowser.open(login_url)
        logger.info("Waiting for you to complete login in the browser...")
        for _ in range(120):
            if auth_result["code"] or auth_result["error"]:
                break
            time.sleep(0.5)

        if auth_result["error"]:
            logger.error(f"OAuth error: {auth_result['error']}")
            raise RuntimeError(f"OAuth authorization failed: {auth_result['error']}")
        if not auth_result["code"]:
            raise RuntimeError("Timeout: no callback received. Complete login in the browser and try again.")
        if auth_result["state"] != state:
            raise RuntimeError("OAuth state mismatch. Please try again.")

        # Exchange the authorization code for an access token.
        data = {
            "grant_type": "authorization_code",
            "code": auth_result["code"],
            "redirect_uri": redirect_uri,
            "client_id": client_id,
            "client_secret": client_secret,
            "code_verifier": code_verifier,
        }
        resp = requests.post(
            token_url,
            data=data,
            headers={"Content-Type": "application/x-www-form-urlencoded"},
            timeout=30,
        )
        if resp.status_code >= 400:
            logger.error(f"Token exchange failed: HTTP {resp.status_code} - {resp.text[:500]}")
            raise RuntimeError(f"Token exchange failed: {resp.text[:200]}")
        out = resp.json()
        access_token = out.get("access_token") or out.get("accessToken")
        if not access_token:
            raise RuntimeError("Token response did not contain access_token")
        return access_token
    finally:
        try:
            server.server_close()
        except Exception:
            pass


# -------------------------------------------------------------------------
# Token Resolution
# -------------------------------------------------------------------------
# Resolve a Bearer token for API calls: prefer static token from environment,
# then fall back to OAuth browser flow when client credentials are configured.
# -------------------------------------------------------------------------


def get_bearer_token(server_url: str) -> str:
    """
    Resolve a valid Bearer token using the configured authentication method.

    Resolution order:

    1. `PIPESHUB_BEARER_AUTH` (static token from environment)
    2. OAuth 2.0 Authorization Code Flow with PKCE using
       `PIPESHUB_OAUTH_CLIENT_ID` and `PIPESHUB_OAUTH_CLIENT_SECRET`

    Parameters
    ----------
    server_url : str
        Base URL of the PipesHub API (used for OAuth endpoints when applicable).

    Returns
    -------
    str
        Bearer token string for the Authorization header.

    Raises
    ------
    RuntimeError
        When neither a static token nor OAuth credentials are configured, or
        when OAuth flow fails (e.g. user denial, timeout, token exchange error).
    """
    # Prefer static Bearer token from environment when set.
    token = (os.getenv("PIPESHUB_BEARER_AUTH") or "").strip()
    if token:
        return token

    # Otherwise use OAuth: client ID and secret must be configured.
    client_id = (os.getenv("PIPESHUB_OAUTH_CLIENT_ID") or "").strip()
    client_secret = (os.getenv("PIPESHUB_OAUTH_CLIENT_SECRET") or "").strip()
    if client_id and client_secret:
        redirect_port = int(
            os.getenv("PIPESHUB_OAUTH_REDIRECT_PORT", str(DEFAULT_OAUTH_REDIRECT_PORT)).strip()
            or str(DEFAULT_OAUTH_REDIRECT_PORT)
        )
        return _oauth_flow_browser(server_url, client_id, client_secret, redirect_port)

    logger.error(
        "No auth configured. Set either PIPESHUB_BEARER_AUTH or (PIPESHUB_OAUTH_CLIENT_ID and PIPESHUB_OAUTH_CLIENT_SECRET). "
        "Create an OAuth app in PipesHub and use its client ID/secret; redirect URI: http://localhost:8765/callback"
    )
    raise RuntimeError("Missing auth: set PIPESHUB_BEARER_AUTH or OAuth client credentials.")


# -------------------------------------------------------------------------
# List Agents via API
# -------------------------------------------------------------------------
# This example calls GET /agents with the resolved Bearer token and prints
# the result. The response is normalized to a list so that both raw-list and
# wrapper (e.g. {"data": [...]}) API shapes are handled consistently.
# -------------------------------------------------------------------------


def list_agents_via_api(server_url: str, token: str) -> list:
    """
    Call GET /agents and return a list of agent objects.

    Normalizes the API response: if the API returns a wrapper (e.g.
    `{"data": [...]}`), the inner list is extracted so callers always
    receive a list. If the response has no recognizable list shape,
    an empty list is returned.

    Parameters
    ----------
    server_url : str
        PipesHub API base URL (trailing slash is stripped if present).

    token : str
        Bearer token for the Authorization header.

    Returns
    -------
    list
        List of agent dicts (or objects). Empty list if the response has
        no list shape.

    Raises
    ------
    RuntimeError
        When the request returns an HTTP error (status >= 400).
    """
    base = server_url.rstrip("/")
    resp = requests.get(
        f"{base}/agents",
        headers={"Authorization": f"Bearer {token}", "Content-Type": "application/json"},
        timeout=30,
    )
    if resp.status_code >= 400:
        raise RuntimeError(f"List agents failed: HTTP {resp.status_code} - {resp.text[:500]}")
    data = resp.json()
    # API may return a raw list or a wrapper (e.g. {"data": [...]}); normalize to a list for callers.
    if isinstance(data, list):
        return data
    for key in ("data", "agents", "result"):
        if isinstance(data.get(key), list):
            return data[key]
    return []


# -------------------------------------------------------------------------
# Script Entrypoint
# -------------------------------------------------------------------------


def main() -> None:
    """
    CLI entrypoint: authenticate, call GET /agents, and print the result.

    The script resolves a Bearer token (from environment or OAuth), fetches
    the list of agents for the authenticated user, and logs the result as
    JSON. The full token is not logged to avoid accidental leakage.
    """
    server_url = os.getenv("PIPESHUB_SERVER_URL", DEFAULT_SERVER_URL).strip() or DEFAULT_SERVER_URL
    token = get_bearer_token(server_url)
    logger.info("Listing agents...")
    agents = list_agents_via_api(server_url, token)
    # Pretty-print list (or empty array) for developer visibility.
    logger.json("Agents", agents if agents else [])


if __name__ == "__main__":
    main()
