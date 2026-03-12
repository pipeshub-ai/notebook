"""
Full flow script: authenticate → create a new agent → start chat REPL (all in one process).

Use this when you want the complete sequence without switching between examples.
  Run: python src/index.py   (from agent_example directory)

Provides create_agent_via_api() which is also used by the create-agent and chat-with-agent
examples to perform POST /agents/create.
"""
import os
import sys
import time
from typing import Any, Optional

_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, _root)

import requests
from dotenv import load_dotenv

from src.auth import get_bearer_token
from src.logger import logger

load_dotenv()

DEFAULT_SERVER_URL = "https://app.pipeshub.com/api/v1"
AGENT_NAME_PREFIX = "SDK Demo Agent"


def get_pipeshub_client(server_url: str, token: str) -> Any:
    """Build a Pipeshub SDK client (context manager). Used for model discovery and (in examples) agent creation."""
    from pipeshub_sdk import Pipeshub, models
    return Pipeshub(
        security=models.Security(bearer_auth=token),
        server_url=server_url,
    )


def get_available_models_by_type(pipeshub: Any, model_type: str) -> list:
    """Return available AI models for the given type ('llm' or 'reasoning') from SDK."""
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
    models = getattr(res, "models", None) or (res.get("models") if isinstance(res, dict) else None)
    return list(models) if models else []


def get_available_models_via_api(server_url: str, token: str, model_type: str) -> list:
    """Fallback: GET /configurationManager/ai-models/available/{modelType} when SDK has no models."""
    base = server_url.rstrip("/")
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
    models = data.get("models") if isinstance(data, dict) else None
    return list(models) if isinstance(models, list) else []


def pick_llm_and_reasoning(
    pipeshub: Any,
    server_url: Optional[str] = None,
    token: Optional[str] = None,
) -> list:
    """Build models payload for agent create (prefer GPT-4o; fallback to defaults)."""
    llm_models = get_available_models_by_type(pipeshub, "llm")
    reasoning_models = get_available_models_by_type(pipeshub, "reasoning")
    if not llm_models and not reasoning_models and server_url and token:
        llm_models = get_available_models_via_api(server_url, token, "llm")
        reasoning_models = get_available_models_via_api(server_url, token, "reasoning")

    def first_model(models: list, prefer_key: Optional[str] = None):
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
        key = getattr(m, "model_key", None) or m.get("modelKey") or ""
        provider = getattr(m, "provider", None) or m.get("provider") or ""
        model_name = getattr(m, "model", None) or m.get("model") or key
        return {
            "modelKey": key,
            "provider": provider,
            "modelName": model_name,
            "isReasoning": is_reasoning,
        }

    llm = first_model(llm_models, "gpt-4o") or first_model(llm_models)
    reasoning = first_model(reasoning_models, "gpt-4o") or first_model(reasoning_models) or llm

    if not llm and not reasoning:
        return []

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
    """GET /agents and return a list of agents (handles wrapped response shapes)."""
    base = server_url.rstrip("/")
    resp = requests.get(
        f"{base}/agents",
        headers={"Authorization": f"Bearer {token}", "Content-Type": "application/json"},
        timeout=30,
    )
    if resp.status_code >= 400:
        raise RuntimeError(f"List agents failed: HTTP {resp.status_code} - {resp.text[:500]}")
    data = resp.json()
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
    POST /agents/create with the given name, description, prompts, and model_entries.
    Returns the new agent's key (_key or key or id from response.agent).
    Exits on HTTP or parse error.
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
    """Create a new agent with a unique name (timestamped). Returns agent_key. Used by the full-flow REPL."""
    from datetime import datetime
    agent_name = f"{AGENT_NAME_PREFIX} ({datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')} UTC)"

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
    """POST /agents/{agent_key}/conversations; returns (conversation_id, conversation_dict)."""
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
    """POST /agents/{agent_key}/conversations/{conversation_id}/messages; returns conversation dict."""
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
    """GET /agents/{agent_key}/conversations/{conversation_id}; returns conversation dict."""
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
    """From a raw API conversation dict, return the last bot_response message content."""
    if not data or not isinstance(data, dict):
        return None
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
    Interactive REPL: read user message, send to agent conversation API, print reply.
    First message creates the conversation; later messages POST to .../messages.
    If reply is not in the response, poll GET conversation until COMPLETED/FAILED or content appears.
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


def main() -> None:
    """Full flow: auth → create one new agent (timestamped name) → chat REPL until quit/exit."""
    server_url = os.getenv("PIPESHUB_SERVER_URL", DEFAULT_SERVER_URL).strip() or DEFAULT_SERVER_URL
    token = get_bearer_token(server_url)
    with get_pipeshub_client(server_url, token) as pipeshub:
        agent_key = create_agent(pipeshub, server_url, token)
        run_repl(pipeshub, agent_key, server_url, token)


if __name__ == "__main__":
    main()
