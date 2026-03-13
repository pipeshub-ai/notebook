"""
PipesHub Authentication Helper
==============================

This module provides a simple way to obtain a Bearer token for making
authenticated requests to the PipesHub API.

Two authentication strategies are supported:

1. Static Bearer Token
   If the environment variable `PIPESHUB_BEARER_AUTH` is present,
   the token will be used directly without invoking OAuth.

2. OAuth 2.0 Authorization Code Flow with PKCE
   If a bearer token is not available, the module falls back to the OAuth flow.
   A browser window is opened for user login, and a temporary local HTTP server
   listens for the OAuth redirect containing the authorization code.

The code is then exchanged for an access token which can be used for
subsequent API calls.

Typical usage:

    python examples/auth/index.py
    python main.py auth
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
    """

    base = server_url.rstrip("/")
    authorize_url = f"{base}/oauth2/authorize"
    token_url = f"{base}/oauth2/token"

    redirect_uri = f"http://localhost:{redirect_port}{OAUTH_CALLBACK_PATH}"

    # -----------------------------------------------------------------
    # OAuth state protects against CSRF attacks
    # PKCE values protect the authorization code exchange
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
                self._send(400, "Invalid callback path")
                return

            query = parse_qs(parsed.query)

            if "error" in query:
                auth_result["error"] = query["error"][0]
                self._send(200, "Login failed. You may close this tab.")
                return

            if "code" not in query:
                self._send(400, "Missing authorization code")
                return

            auth_result["code"] = query["code"][0]
            auth_result["state"] = (query.get("state") or [None])[0]

            self._send(200, "Login successful. You may close this tab.")

        def _send(self, code: int, message: str) -> None:
            self.send_response(code)
            self.send_header("Content-type", "text/html; charset=utf-8")
            self.end_headers()
            self.wfile.write(f"<h1>{message}</h1>".encode("utf-8"))

        def log_message(self, format: str, *args: Any) -> None:
            # Disable default HTTP server logging
            pass

    # Start callback listener
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
        logger.info("Opening browser for PipesHub login")
        webbrowser.open(login_url)

        logger.info("Waiting for OAuth callback...")

        for _ in range(120):
            if auth_result["code"] or auth_result["error"]:
                break
            time.sleep(0.5)

        if auth_result["error"]:
            raise RuntimeError(f"OAuth authorization failed: {auth_result['error']}")

        if not auth_result["code"]:
            raise RuntimeError("OAuth login timeout")

        if auth_result["state"] != state:
            raise RuntimeError("OAuth state mismatch")

        token_response = requests.post(
            token_url,
            data={
                "grant_type": "authorization_code",
                "code": auth_result["code"],
                "redirect_uri": redirect_uri,
                "client_id": client_id,
                "client_secret": client_secret,
                "code_verifier": code_verifier,
            },
            headers={"Content-Type": "application/x-www-form-urlencoded"},
            timeout=30,
        )

        if token_response.status_code >= 400:
            raise RuntimeError("Token exchange failed")

        payload = token_response.json()

        access_token = payload.get("access_token") or payload.get("accessToken")

        if not access_token:
            raise RuntimeError("Access token missing from response")

        return access_token

    finally:
        try:
            server.server_close()
        except Exception:
            pass


# -------------------------------------------------------------------------
# Token Resolution
# -------------------------------------------------------------------------


def get_bearer_token(server_url: str) -> str:
    """
    Resolve a valid Bearer token using the configured authentication method.

    Resolution order:

    1. `PIPESHUB_BEARER_AUTH`
    2. OAuth client credentials
    """

    token = (os.getenv("PIPESHUB_BEARER_AUTH") or "").strip()

    if token:
        return token

    client_id = (os.getenv("PIPESHUB_OAUTH_CLIENT_ID") or "").strip()
    client_secret = (os.getenv("PIPESHUB_OAUTH_CLIENT_SECRET") or "").strip()

    if client_id and client_secret:
        redirect_port = int(
            os.getenv("PIPESHUB_OAUTH_REDIRECT_PORT", str(DEFAULT_OAUTH_REDIRECT_PORT))
        )

        return _oauth_flow_browser(server_url, client_id, client_secret, redirect_port)

    raise RuntimeError(
        "Authentication not configured. Set PIPESHUB_BEARER_AUTH or OAuth credentials."
    )


# -------------------------------------------------------------------------
# Script Entrypoint
# -------------------------------------------------------------------------


def main() -> None:
    """
    Simple CLI entrypoint used to test authentication.

    The script resolves a bearer token and prints a shortened prefix of it.
    The full token is intentionally not logged to prevent accidental leakage.
    """

    server_url = os.getenv("PIPESHUB_SERVER_URL", DEFAULT_SERVER_URL)

    try:
        token = get_bearer_token(server_url)
    except RuntimeError as exc:
        logger.error(str(exc))
        sys.exit(1)

    logger.info("Bearer token acquired", token[:20] + "...")


if __name__ == "__main__":
    main()