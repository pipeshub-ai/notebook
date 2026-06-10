"""
Create Agent Example
====================

This example creates a new PipesHub Agent via the API endpoint
POST /agents/create. Each run creates a new agent with a fixed display
name; the script does not look up or reuse existing agents by name.

Authentication and model selection:

1. Static Bearer Token or OAuth with PKCE
   Authentication follows the same approach as the auth example: use
   `PIPESHUB_BEARER_AUTH` for a static token, or OAuth client credentials
   for browser-based login.

2. Model discovery and agent creation
   The script builds a PipesHub SDK client for model discovery, selects
   the first available LLM and reasoning models (preferring GPT-4o when
   available), then calls the shared helper `create_agent_via_api()` from
   `src/index.py` to perform POST /agents/create.

Typical usage:

    python examples/create-agent/index.py
    python main.py create-agent
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
# the project source directory (e.g. `src.logger`, `src.index`).
# Without this adjustment, Python would not resolve the imports correctly.
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

# Display name of the agent created by this example on each run (new agent every run).
AGENT_NAME = "SDK Demo Agent"


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
    token = (os.getenv("PIPESHUB_BEARER_AUTH") or "").strip()
    if token:
        return token

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
# Create Agent via API (model discovery + POST /agents/create)
# -------------------------------------------------------------------------
# This example: (1) Build SDK client for model discovery. (2) Pick LLM and
# reasoning models (prefer GPT-4o). (3) Call create_agent_via_api() in
# src/index.py to perform POST /agents/create.
# -------------------------------------------------------------------------


def get_pipeshub_client(server_url: str, token: str) -> Any:
    """
    Build a PipesHub SDK client for use as a context manager.

    The client is used here for model discovery (available LLM and reasoning
    models). The actual agent creation is performed via REST in
    create_agent_via_api().

    Parameters
    ----------
    server_url : str
        PipesHub API base URL.

    token : str
        Bearer token for authentication.

    Returns
    -------
    Any
        Pipeshub client instance; use as context manager (with ... as client).
    """
    from pipeshub_sdk import Pipeshub, models
    return Pipeshub(
        security=models.Security(bearer_auth=token),
        server_url=server_url,
    )


def get_available_models_by_type(pipeshub: Any, model_type: str) -> list:
    """
    Get available AI models from the SDK for a given type.

    Parameters
    ----------
    pipeshub : Any
        PipesHub SDK client (from get_pipeshub_client).

    model_type : str
        One of 'llm' or 'reasoning'.

    Returns
    -------
    list
        List of model objects or dicts. Empty list if the SDK has no
        corresponding API or returns nothing.
    """
    # Try SDK: different SDK versions may expose configuration_manager or ai_models_providers.
    try:
        if hasattr(pipeshub, "configuration_manager"):
            res = pipeshub.configuration_manager.get_available_models_by_type(model_type=model_type)
        elif hasattr(pipeshub, "ai_models_providers"):
            res = pipeshub.ai_models_providers.get_available_models_by_type(model_type=model_type)
        else:
            return []
    except Exception:
        return []
    if res is None:
        return []
    # Response may be an object with .models or a dict with "models" key.
    models = getattr(res, "models", None) or (res.get("models") if isinstance(res, dict) else None)
    return list(models) if models else []


def get_available_models_via_api(server_url: str, token: str, model_type: str) -> list:
    """
    Fetch available models via REST when the SDK returns nothing.

    Fallback for environments where the SDK does not expose or populate
    model lists; calls GET .../configurationManager/ai-models/available/{model_type}.

    Parameters
    ----------
    server_url : str
        PipesHub API base URL.

    token : str
        Bearer token for the request.

    model_type : str
        One of 'llm' or 'reasoning'.

    Returns
    -------
    list
        List of model dicts from the response models field. Empty list on
        HTTP error or when the response has no models.
    """
    base = server_url.rstrip("/")
    # Fallback: call REST endpoint when SDK returns no models.
    resp = requests.get(
        f"{base}/configurationManager/ai-models/available/{model_type}",
        headers={"Authorization": f"Bearer {token}", "Content-Type": "application/json"},
        timeout=30,
    )
    if resp.status_code >= 400:
        return []
    try:
        data = resp.json()
    except ValueError:
        return []
    # API response shape: { "models": [ ... ] }.
    models = data.get("models") if isinstance(data, dict) else None
    return list(models) if isinstance(models, list) else []


def pick_llm_and_reasoning(
    pipeshub: Any,
    server_url: Optional[str] = None,
    token: Optional[str] = None,
) -> list:
    """
    Build the models payload for POST /agents/create.

    Selects one LLM and optionally a reasoning model. Prefers GPT-4o when
    available; otherwise uses the first default or the first in the list.
    If the SDK returns no models, falls back to get_available_models_via_api.

    Parameters
    ----------
    pipeshub : Any
        PipesHub SDK client (for model discovery).

    server_url : str, optional
        Used for REST API fallback when the SDK returns no models.

    token : str, optional
        Used for REST API fallback.

    Returns
    -------
    list
        List of dicts with keys modelKey, provider, modelName, isReasoning,
        suitable for the create agent API. Empty list if no models are found.
    """
    llm_models = get_available_models_by_type(pipeshub, "llm")
    reasoning_models = get_available_models_by_type(pipeshub, "reasoning")
    # If SDK returns nothing, try REST API (e.g. GET .../ai-models/available/llm).
    if not llm_models and not reasoning_models and server_url and token:
        llm_models = get_available_models_via_api(server_url, token, "llm")
        reasoning_models = get_available_models_via_api(server_url, token, "reasoning")

    def first_model(models: list, prefer_key: Optional[str] = None):
        """Pick one model: optional prefer_key (e.g. 'gpt-4o'), else first default, else first in list."""
        if not models:
            return None
        if prefer_key:
            for m in models:
                key = (getattr(m, "model_key", None) or m.get("modelKey") or "").lower()
                model_name = (getattr(m, "model", None) or m.get("model") or "").lower()
                if prefer_key in key or prefer_key in model_name:
                    return m
        for m in models:
            if getattr(m, "is_default", None) or m.get("isDefault"):
                return m
        return models[0]

    def to_entry(m: Any, is_reasoning: bool) -> dict:
        """Convert SDK/API model object to dict expected by POST /agents/create."""
        key = getattr(m, "model_key", None) or m.get("modelKey") or ""
        provider = getattr(m, "provider", None) or m.get("provider") or ""
        model_name = getattr(m, "model", None) or m.get("model") or key
        return {
            "modelKey": key,
            "provider": provider,
            "modelName": model_name,
            "isReasoning": is_reasoning,
        }

    # Prefer GPT-4o when available; otherwise first default or first in list.
    llm = first_model(llm_models, "gpt-4o") or first_model(llm_models)
    reasoning = first_model(reasoning_models, "gpt-4o") or first_model(reasoning_models) or llm

    if not llm and not reasoning:
        return []

    # Build list of model entries; avoid duplicating the same model as both LLM and reasoning.
    entries = []
    llm_key = (getattr(llm, "model_key", None) or llm.get("modelKey") if llm else None) or ""
    reasoning_key = (getattr(reasoning, "model_key", None) or reasoning.get("modelKey") if reasoning else None) or ""
    if llm:
        entries.append(to_entry(llm, is_reasoning=False))
    if reasoning and (not llm or reasoning_key != llm_key):
        entries.append(to_entry(reasoning, is_reasoning=True))
    # API expects at least one model marked as reasoning.
    if entries and not any(e.get("isReasoning") for e in entries):
        entries[0]["isReasoning"] = True
    return entries


def create_agent(pipeshub: Any, server_url: str, token: str) -> str:
    """
    Create a new agent and return its key.

    Picks LLM and reasoning models via pick_llm_and_reasoning(), then calls
    create_agent_via_api() from src/index.py to perform POST /agents/create.
    Does not look up or reuse existing agents by name; each run creates a
    new agent.

    Parameters
    ----------
    pipeshub : Any
        SDK client used for model discovery.

    server_url : str
        PipesHub API base URL.

    token : str
        Bearer token for API requests.

    Returns
    -------
    str
        The new agent's key (string).

    Exits
    -----
    sys.exit(1) when no AI models are found or when the create API returns
    an error.
    """
    # Discover LLM and reasoning models; exit if none are configured in PipesHub.
    model_entries = pick_llm_and_reasoning(pipeshub, server_url, token)
    if not model_entries:
        logger.error(
            "No AI models found. Configure LLM and reasoning models in PipesHub (Settings → AI Models)."
        )
        sys.exit(1)

    # Shared helper in src/index.py: performs POST /agents/create.
    from src.index import create_agent_via_api

    logger.info(f"Creating agent '{AGENT_NAME}' with models: {[e.get('modelKey') for e in model_entries]}")
    key = create_agent_via_api(
        server_url=server_url,
        token=token,
        name=AGENT_NAME,
        description="Demo agent created by pipeshub-sdk agent_example",
        system_prompt="You are a helpful assistant.",
        start_message="Hello! How can I help you today?",
        model_entries=model_entries,
    )
    logger.info(f"Created agent: {AGENT_NAME} ({key})")
    return str(key)


# -------------------------------------------------------------------------
# Script Entrypoint
# -------------------------------------------------------------------------


def main() -> None:
    """
    CLI entrypoint: authenticate, create one agent, and print its key.

    The script resolves a Bearer token, builds an SDK client for model
    discovery, creates a new agent via the shared create_agent_via_api()
    REST helper, and logs the agent key for use in chat or other API calls.
    """
    server_url = os.getenv("PIPESHUB_SERVER_URL", DEFAULT_SERVER_URL).strip() or DEFAULT_SERVER_URL
    token = get_bearer_token(server_url)
    # SDK client used only for model discovery; actual create is via REST in create_agent_via_api.
    with get_pipeshub_client(server_url, token) as pipeshub:
        agent_key = create_agent(pipeshub, server_url, token)
    logger.info("Agent key (use this for chat or API calls): " + str(agent_key))


if __name__ == "__main__":
    main()
