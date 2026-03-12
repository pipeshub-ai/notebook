"""
Shared authentication for the agent_example sample.

Provides a single entrypoint: get_bearer_token(server_url).
- If PIPESHUB_BEARER_AUTH is set in the environment, that token is returned.
- Otherwise, if OAuth credentials are set (PIPESHUB_OAUTH_CLIENT_ID / PIPESHUB_OAUTH_CLIENT_SECRET),
  runs the OAuth 2.0 Authorization Code flow with PKCE: opens the default browser for login,
  runs a local HTTP server to receive the redirect, then exchanges the code for an access token.

Used by all examples (auth, list-agents, create-agent, chat-with-agent) and by src/index.py.
"""
import base64
import hashlib
import os
import secrets
import threading
import time
import webbrowser
from http.server import BaseHTTPRequestHandler, HTTPServer
from typing import Any, Dict, Optional
from urllib.parse import parse_qs, urlencode, urlparse

import requests
from dotenv import load_dotenv

from src.logger import logger

load_dotenv()

# -----------------------------------------------------------------------------
# Constants (override via env: PIPESHUB_SERVER_URL, PIPESHUB_OAUTH_REDIRECT_PORT)
# -----------------------------------------------------------------------------
DEFAULT_SERVER_URL = "https://app.pipeshub.com/api/v1"
DEFAULT_OAUTH_SCOPES = "openid profile email offline_access"
DEFAULT_OAUTH_REDIRECT_PORT = 8765
OAUTH_CALLBACK_PATH = "/callback"


# -----------------------------------------------------------------------------
# PKCE helpers (RFC 7636) – required by PipesHub OAuth2
# -----------------------------------------------------------------------------

def _pkce_code_verifier() -> str:
    """Generate a cryptographically random PKCE code verifier (base64url, 43 bytes)."""
    return secrets.token_urlsafe(43)


def _pkce_code_challenge(verifier: str) -> str:
    """Compute S256 code challenge: BASE64URL(SHA256(verifier))."""
    digest = hashlib.sha256(verifier.encode("utf-8")).digest()
    return base64.urlsafe_b64encode(digest).decode("utf-8").rstrip("=")


# -----------------------------------------------------------------------------
# OAuth 2.0 Authorization Code flow with PKCE (browser + local callback)
# -----------------------------------------------------------------------------

def _oauth_flow_browser(server_url: str, client_id: str, client_secret: str, redirect_port: int) -> str:
    """
    Run the full OAuth 2.0 flow: build authorize URL with PKCE, open browser, start a one-request
    HTTP server on localhost for the redirect, wait for callback, then exchange code for tokens.

    Returns:
        The access_token from the token endpoint (suitable as Bearer token for PipesHub API).

    Raises:
        RuntimeError: On OAuth error, timeout, state mismatch, or token exchange failure.
    """
    base = server_url.rstrip("/")
    authorize_url = f"{base}/oauth2/authorize"
    token_url = f"{base}/oauth2/token"
    redirect_uri = f"http://localhost:{redirect_port}{OAUTH_CALLBACK_PATH}"

    # CSRF protection and PKCE
    state = secrets.token_urlsafe(32)
    code_verifier = _pkce_code_verifier()
    code_challenge = _pkce_code_challenge(code_verifier)

    # Shared state read by the callback handler and by this function after the request
    auth_result: Dict[str, Optional[str]] = {"code": None, "state": None, "error": None}

    class CallbackHandler(BaseHTTPRequestHandler):
        """Handles GET request to /callback: captures ?code= and ?state= or ?error= from PipesHub redirect."""

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
            pass

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
        for _ in range(120):  # Poll up to 60 seconds
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

        # Exchange authorization code for access token (with code_verifier for PKCE)
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


# -----------------------------------------------------------------------------
# Public API
# -----------------------------------------------------------------------------

def get_bearer_token(server_url: str) -> str:
    """
    Obtain a Bearer token for the PipesHub API.

    Resolution order:
      1. If PIPESHUB_BEARER_AUTH is set, return it (no browser, no OAuth).
      2. If PIPESHUB_OAUTH_CLIENT_ID and PIPESHUB_OAUTH_CLIENT_SECRET are set, run the OAuth
         browser flow (opens login page, local callback, then returns access_token).
      3. Otherwise raise RuntimeError with instructions.

    Args:
        server_url: PipesHub API base URL (e.g. https://app.pipeshub.com/api/v1).

    Returns:
        A string token to use as Authorization: Bearer <token>.

    Raises:
        RuntimeError: When no auth is configured or OAuth fails.
    """
    token = (os.getenv("PIPESHUB_BEARER_AUTH") or "").strip()
    if token:
        return token

    client_id = (os.getenv("PIPESHUB_OAUTH_CLIENT_ID") or "").strip()
    client_secret = (os.getenv("PIPESHUB_OAUTH_CLIENT_SECRET") or "").strip()
    if client_id and client_secret:
        redirect_port = int(os.getenv("PIPESHUB_OAUTH_REDIRECT_PORT", str(DEFAULT_OAUTH_REDIRECT_PORT)).strip() or str(DEFAULT_OAUTH_REDIRECT_PORT))
        return _oauth_flow_browser(server_url, client_id, client_secret, redirect_port)

    logger.error(
        "No auth configured. Set either PIPESHUB_BEARER_AUTH or (PIPESHUB_OAUTH_CLIENT_ID and PIPESHUB_OAUTH_CLIENT_SECRET). "
        "Create an OAuth app in PipesHub and use its client ID/secret; redirect URI: http://localhost:8765/callback"
    )
    raise RuntimeError("Missing auth: set PIPESHUB_BEARER_AUTH or OAuth client credentials.")
