"""
Full-Flow Agent Example (src)
============================

This module runs the complete agent flow in a single process: authenticate,
create one agent, then run an interactive chat REPL. Use it when you want
the full sequence without switching between separate examples.

It also exports create_agent_via_api(), which the create-agent and
chat-with-agent examples import to perform POST /agents/create. That
shared helper is the single implementation of agent creation via the REST
API; the examples use it to avoid duplicating request logic.

Authentication uses the same approach as the auth example (static Bearer
token or OAuth 2.0 Authorization Code Flow with PKCE).

Typical usage:

    python src/index.py
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

# -------------------------------------------------------------------------
# Project Path Setup
# -------------------------------------------------------------------------
# This ensures that running this script directly (from agent_example or
# from agent_example/src) still allows imports from the project root
# (e.g. src.logger). The path is one level up from src/ so the parent
# directory is agent_example.
# -------------------------------------------------------------------------

_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, _root)

import requests
from dotenv import load_dotenv

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

# Prefix for the full-flow agent name; a timestamp is appended so each
# run creates a distinct agent (e.g. "SDK Demo Agent (2025-03-13 12:00:00 UTC)").
AGENT_NAME_PREFIX = "SDK Demo Agent"


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
# Full Flow: SDK Client, Model Discovery, create_agent_via_api, Conversation API, REPL
# -------------------------------------------------------------------------
# create_agent_via_api() below is the shared implementation of POST /agents/create;
# the create-agent and chat-with-agent examples import it from this module.
# -------------------------------------------------------------------------


def get_pipeshub_client(server_url: str, token: str) -> Any:
    """
    Build a PipesHub SDK client for use as a context manager.

    Used for model discovery when creating an agent. The actual agent
    creation is performed via create_agent_via_api() (REST).

    Parameters
    ----------
    server_url : str
        PipesHub API base URL.

    token : str
        Bearer token for authentication.

    Returns
    -------
    Any
        Pipeshub client instance; use with 'with ... as client'.
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

    Fallback: GET .../configurationManager/ai-models/available/{model_type}.

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
    Build the models payload for agent create (prefer GPT-4o; fallback to defaults).

    Selects one LLM and optionally a reasoning model. If the SDK returns
    no models, falls back to get_available_models_via_api.

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
        List of dicts with modelKey, provider, modelName, isReasoning.
        Empty list if no models found.
    """
    llm_models = get_available_models_by_type(pipeshub, "llm")
    reasoning_models = get_available_models_by_type(pipeshub, "reasoning")
    # Fallback to REST API when SDK returns no models.
    if not llm_models and not reasoning_models and server_url and token:
        llm_models = get_available_models_via_api(server_url, token, "llm")
        reasoning_models = get_available_models_via_api(server_url, token, "reasoning")

    def first_model(models: list, prefer_key: Optional[str] = None):
        """Pick one model: prefer_key match, else first default, else first in list."""
        if not models:
            return None
        for m in models:
            key = (getattr(m, "model_key", None) or m.get("modelKey") or "").lower()
            model_name = (getattr(m, "model", None) or m.get("model") or "").lower()
            if prefer_key and (prefer_key in key or prefer_key in model_name):
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

    # Prefer GPT-4o when available.
    llm = first_model(llm_models, "gpt-4o") or first_model(llm_models)
    reasoning = first_model(reasoning_models, "gpt-4o") or first_model(reasoning_models) or llm

    if not llm and not reasoning:
        return []

    # Build model list; avoid duplicate if same model is both LLM and reasoning.
    entries = []
    llm_key = (getattr(llm, "model_key", None) or llm.get("modelKey") if llm else None) or ""
    reasoning_key = (getattr(reasoning, "model_key", None) or reasoning.get("modelKey") if reasoning else None) or ""
    if llm:
        entries.append(to_entry(llm, is_reasoning=False))
    if reasoning and (not llm or reasoning_key != llm_key):
        entries.append(to_entry(reasoning, is_reasoning=True))
    if entries and not any(e.get("isReasoning") for e in entries):
        entries[0]["isReasoning"] = True
    return entries


def list_agents_via_api(server_url: str, token: str) -> list:
    """
    Call GET /agents and return a list of agents.

    Normalizes the response: if the API returns a wrapper (e.g.
    `{"data": [...]}`), the inner list is returned so callers get a
    consistent list shape.

    Parameters
    ----------
    server_url : str
        PipesHub API base URL.

    token : str
        Bearer token for the request.

    Returns
    -------
    list
        List of agent dicts. Empty list if the response has no list shape.

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


def create_agent_via_api(
    server_url: str,
    token: str,
    name: str,
    description: str,
    system_prompt: str,
    start_message: str,
    model_entries: list,
) -> str:
    """
    Create an agent via POST /agents/create.

    This function is shared by this script and by the create-agent and
    chat-with-agent examples. It is the single implementation of agent
    creation via the REST API.

    Parameters
    ----------
    server_url : str
        PipesHub API base URL.

    token : str
        Bearer token for the request.

    name : str
        Agent display name.

    description : str
        Agent description.

    system_prompt : str
        System prompt for the agent.

    start_message : str
        Initial greeting message.

    model_entries : list
        List of dicts with keys modelKey, provider, modelName, isReasoning
        (from pick_llm_and_reasoning or equivalent).

    Returns
    -------
    str
        The new agent's key (string).

    Exits
    -----
    sys.exit(1) on HTTP error, non-JSON response, or missing agent/key
    in the response.
    """
    base = server_url.rstrip("/")
    resp = requests.post(
        f"{base}/agents/create",
        headers={"Authorization": f"Bearer {token}", "Content-Type": "application/json"},
        json={
            "name": name,
            "description": description,
            "systemPrompt": system_prompt,
            "startMessage": start_message,
            "models": model_entries,
            "toolsets": [],
            "knowledge": [],
        },
        timeout=60,
    )
    if resp.status_code >= 400:
        logger.error(f"Create agent failed: HTTP {resp.status_code} - {resp.text[:500]}")
        sys.exit(1)
    try:
        data = resp.json()
    except ValueError:
        logger.error("Create agent returned non-JSON response.")
        sys.exit(1)
    # Response shape: { "agent": { "_key" or "key" or "id": ... } }.
    agent = data.get("agent") if isinstance(data, dict) else None
    if not isinstance(agent, dict):
        logger.error("Create agent response missing 'agent' object.")
        sys.exit(1)
    key = agent.get("_key") or agent.get("key") or agent.get("id")
    if not key:
        logger.error("Create agent response missing agent._key. Keys: " + str(list(agent.keys())))
        sys.exit(1)
    return str(key)


def create_agent(pipeshub: Any, server_url: str, token: str) -> str:
    """
    Create one agent with a timestamped name and return its key.

    Uses AGENT_NAME_PREFIX plus a UTC timestamp so each execution creates
    a distinct agent. Picks LLM and reasoning models, then calls
    create_agent_via_api() to perform POST /agents/create.

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
        The new agent's key.

    Exits
    -----
    sys.exit(1) when no AI models are found or when the create API returns
    an error.
    """
    from datetime import datetime
    # Unique name per run so each execution creates a distinct agent.
    agent_name = f"{AGENT_NAME_PREFIX} ({datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')} UTC)"

    # Discover LLM and reasoning models; exit if none are configured in PipesHub.
    model_entries = pick_llm_and_reasoning(pipeshub, server_url, token)
    if not model_entries:
        logger.error(
            "No AI models found. Configure LLM and reasoning models in PipesHub (Settings → AI Models)."
        )
        sys.exit(1)

    logger.info(f"Creating new agent '{agent_name}' with models: {[e.get('modelKey') for e in model_entries]}")
    key = create_agent_via_api(
        server_url=server_url,
        token=token,
        name=agent_name,
        description="Demo agent created by pipeshub-sdk agent_example",
        system_prompt="You are a helpful assistant.",
        start_message="Hello! How can I help you today?",
        model_entries=model_entries,
    )
    logger.info(f"Created agent: {agent_name} ({key})")
    return key


def create_agent_conversation_via_api(
    server_url: str, token: str, agent_key: str, query: str
) -> tuple[Optional[str], Optional[dict]]:
    """
    Start a new conversation: POST .../agents/{agent_key}/conversations with initial query.

    Parameters
    ----------
    server_url : str
        PipesHub API base URL.

    token : str
        Bearer token for the request.

    agent_key : str
        Agent identifier.

    query : str
        First user message to start the conversation.

    Returns
    -------
    tuple of (str or None, dict or None)
        (conversation_id, conversation_dict) on success; (None, None) on
        HTTP error or parse error.
    """
    base = server_url.rstrip("/")
    resp = requests.post(
        f"{base}/agents/{agent_key}/conversations",
        headers={"Authorization": f"Bearer {token}", "Content-Type": "application/json"},
        json={"query": query},
        timeout=60,
    )
    if resp.status_code >= 400:
        return None, None
    try:
        data = resp.json()
    except ValueError:
        return None, None
    conv = data.get("conversation") or data
    cid = conv.get("_id") or conv.get("id") or data.get("conversationId") or data.get("conversation_id")
    return (str(cid) if cid else None, conv if isinstance(conv, dict) else data)


def add_agent_message_via_api(
    server_url: str, token: str, agent_key: str, conversation_id: str, query: str
) -> Optional[dict]:
    """
    Add a user message to an existing conversation.

    POST .../agents/{agent_key}/conversations/{conversation_id}/messages
    with the user query.

    Parameters
    ----------
    server_url : str
        PipesHub API base URL.

    token : str
        Bearer token for the request.

    agent_key : str
        Agent identifier.

    conversation_id : str
        Conversation identifier.

    query : str
        User message to send.

    Returns
    -------
    dict or None
        Updated conversation dict on success; None on HTTP or parse error.
    """
    base = server_url.rstrip("/")
    resp = requests.post(
        f"{base}/agents/{agent_key}/conversations/{conversation_id}/messages",
        headers={"Authorization": f"Bearer {token}", "Content-Type": "application/json"},
        json={"query": query},
        timeout=60,
    )
    if resp.status_code >= 400:
        return None
    try:
        data = resp.json()
    except ValueError:
        return None
    return data.get("conversation") or data


def get_agent_conversation_via_api(
    server_url: str, token: str, agent_key: str, conversation_id: str
) -> Optional[dict]:
    """
    Fetch the current conversation state (GET .../conversations/{conversation_id}).

    Used for polling when the agent reply is asynchronous: call repeatedly
    until the response contains bot content or status COMPLETED/FAILED.

    Parameters
    ----------
    server_url : str
        PipesHub API base URL.

    token : str
        Bearer token for the request.

    agent_key : str
        Agent identifier.

    conversation_id : str
        Conversation identifier.

    Returns
    -------
    dict or None
        Conversation dict on success; None on HTTP or parse error.
    """
    base = server_url.rstrip("/")
    resp = requests.get(
        f"{base}/agents/{agent_key}/conversations/{conversation_id}",
        headers={"Authorization": f"Bearer {token}", "Content-Type": "application/json"},
        timeout=30,
    )
    if resp.status_code >= 400:
        return None
    try:
        data = resp.json()
    except ValueError:
        return None
    return data.get("conversation") or data


def extract_bot_content_from_dict(data: Optional[dict]) -> Optional[str]:
    """
    Extract the latest bot/assistant message content from a conversation response.

    Scans messages in reverse order to find the most recent non-user message.
    Handles messageType/role and nested conversation.messages shapes.

    Parameters
    ----------
    data : dict or None
        Raw API response (conversation dict or wrapper containing messages).

    Returns
    -------
    str or None
        Content string of the latest bot message, or None if none found.
    """
    if not data or not isinstance(data, dict):
        return None
    # Messages may be at top level or under data.conversation.
    messages = data.get("messages")
    if not isinstance(messages, list) and isinstance(data.get("conversation"), dict):
        messages = data["conversation"].get("messages")
    if not isinstance(messages, list):
        return None
    for m in reversed(messages):
        if not isinstance(m, dict):
            continue
        msg_type = (m.get("messageType") or m.get("message_type") or "").lower()
        if msg_type == "user_query":
            continue
        role = (m.get("role") or "").lower()
        if msg_type in ("bot_response", "botresponse") or role in ("assistant", "ai", "bot"):
            content = m.get("content")
            if content:
                return str(content)
        content = m.get("content")
        if content:
            return str(content)
    return None


def run_repl(pipeshub: Any, agent_key: str, server_url: str, token: str) -> None:
    """
    Interactive REPL: read user input, send to conversation API, print agent reply.

    The first user message creates the conversation (POST .../conversations);
    later messages POST to .../conversations/{id}/messages. If the reply is
    not present in the response (async agent), the function polls
    GET .../conversations/{id} until bot content is available or status is
    COMPLETED/FAILED. Type 'quit' or 'exit' to end the loop.

    Parameters
    ----------
    pipeshub : Any
        Unused; kept for signature compatibility with callers.

    agent_key : str
        Agent to chat with.

    server_url : str
        PipesHub API base URL.

    token : str
        Bearer token for API requests.
    """
    conversation_id: Optional[str] = None

    logger.info("\nChat with the agent (type 'quit' or 'exit' to stop).\n")
    while True:
        try:
            user_input = input("> ").strip()
        except EOFError:
            break
        if not user_input:
            continue
        if user_input.lower() in ("quit", "exit"):
            break

        try:
            # First user message creates the conversation; subsequent ones add to it.
            if conversation_id is None:
                cid, data = create_agent_conversation_via_api(server_url, token, agent_key, user_input)
                conversation_id = cid
                res_dict = data
            else:
                res_dict = add_agent_message_via_api(
                    server_url, token, agent_key, conversation_id, user_input
                )
                if res_dict:
                    conversation_id = (
                        res_dict.get("_id") or res_dict.get("id")
                        or res_dict.get("conversationId")
                        or res_dict.get("conversation_id")
                        or conversation_id
                    )

            text = extract_bot_content_from_dict(res_dict) if res_dict else None
            # Async: reply may arrive later; poll GET until we have content or COMPLETED/FAILED.
            if not text and conversation_id:
                deadline = time.monotonic() + 90.0
                while time.monotonic() < deadline:
                    polled = get_agent_conversation_via_api(
                        server_url, token, agent_key, conversation_id
                    )
                    text = extract_bot_content_from_dict(polled) if polled else None
                    if text:
                        break
                    status = (polled or {}).get("status", "")
                    if str(status).upper() in ("COMPLETED", "FAILED"):
                        break
                    time.sleep(2.0)
            if text:
                print(text)
            else:
                logger.info("(No assistant reply in response)")
        except Exception as e:
            logger.error(f"Error: {e}")


# -------------------------------------------------------------------------
# Script Entrypoint
# -------------------------------------------------------------------------


def main() -> None:
    """
    CLI entrypoint: authenticate, create one agent (timestamped name), run chat REPL until quit/exit.

    The script resolves a Bearer token, creates a new agent with a unique
    name for this run, then runs an interactive chat loop. The REPL blocks
    until the user types 'quit' or 'exit'.
    """
    server_url = os.getenv("PIPESHUB_SERVER_URL", DEFAULT_SERVER_URL).strip() or DEFAULT_SERVER_URL
    token = get_bearer_token(server_url)
    with get_pipeshub_client(server_url, token) as pipeshub:
        agent_key = create_agent(pipeshub, server_url, token)
        # REPL blocks until user types quit/exit.
        run_repl(pipeshub, agent_key, server_url, token)


if __name__ == "__main__":
    main()
