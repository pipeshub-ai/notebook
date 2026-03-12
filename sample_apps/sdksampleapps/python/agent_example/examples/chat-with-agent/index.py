"""
Chat-with-agent example: interactive REPL to chat with a PipesHub Agent.

Flow:
  1. Authenticate (env token or OAuth browser).
  2. Create a new agent for this session (no reuse of existing agents).
  3. Start a read-eval loop: user types a message, we POST to create or add to the conversation,
     then print the agent's reply (with optional polling if the response is async).

End the session with 'quit' or 'exit'.

Run from agent_example directory:
  python examples/chat-with-agent/index.py
  python main.py chat-with-agent
"""
import os
import sys
import time
from typing import Any, Optional

_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, _root)

import requests
from dotenv import load_dotenv

from src.auth import get_bearer_token
from src.logger import logger

load_dotenv()

DEFAULT_SERVER_URL = "https://app.pipeshub.com/api/v1"
AGENT_NAME = "SDK Demo Agent"


def get_pipeshub_client(server_url: str, token: str) -> Any:
    """Build a Pipeshub SDK client (context manager). Used here for model discovery when creating the agent."""
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
    """Build models payload for agent create (prefer GPT-4o; fallback to defaults). Same logic as create-agent example."""
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


def create_agent_for_chat(pipeshub: Any, server_url: str, token: str) -> str:
    """Create a new agent for this chat run and return its agent_key. Does not reuse existing agents."""
    model_entries = pick_llm_and_reasoning(pipeshub, server_url, token)
    if not model_entries:
        logger.error(
            "No AI models found. Configure LLM and reasoning models in PipesHub (Settings → AI Models)."
        )
        sys.exit(1)

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


def create_agent_conversation_via_api(
    server_url: str, token: str, agent_key: str, query: str
) -> tuple[Optional[str], Optional[dict]]:
    """POST /agents/{agent_key}/conversations with initial query. Returns (conversation_id, conversation_dict)."""
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
    """POST a new user message to an existing conversation. Returns updated conversation dict."""
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
    """GET conversation by ID (used for polling until agent reply is ready)."""
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
    """From a conversation API response, extract the latest assistant/bot message content for display."""
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
    Read-eval loop: prompt for user input, send to agent conversation API, print reply.
    First message creates the conversation (POST .../conversations); subsequent messages
    use POST .../conversations/{id}/messages. If reply is not in the response, poll GET
    .../conversations/{id} until status is COMPLETED/FAILED or we get bot content.
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
    server_url = os.getenv("PIPESHUB_SERVER_URL", DEFAULT_SERVER_URL).strip() or DEFAULT_SERVER_URL
    token = get_bearer_token(server_url)
    with get_pipeshub_client(server_url, token) as pipeshub:
        agent_key = create_agent_for_chat(pipeshub, server_url, token)
        run_repl(pipeshub, agent_key, server_url, token)  # blocks until user types quit/exit


if __name__ == "__main__":
    main()
