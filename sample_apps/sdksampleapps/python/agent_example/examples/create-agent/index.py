"""
Create-agent example: create a new PipesHub Agent (SDK Demo Agent).

Every run creates a new agent; does not look up or reuse an existing one by name.
Uses the first available LLM and reasoning models (prefers GPT-4o if present);
agent is created via POST /agents/create (see create_agent_via_api in src/index.py).

Run from agent_example directory:
  python examples/create-agent/index.py
  python main.py create-agent
"""
import os
import sys
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
    """Build a Pipeshub SDK client (context manager). Use: with get_pipeshub_client(url, token) as pipeshub: ..."""
    from pipeshub_sdk import Pipeshub, models
    return Pipeshub(
        security=models.Security(bearer_auth=token),
        server_url=server_url,
    )


def get_available_models_by_type(pipeshub: Any, model_type: str) -> list:
    """Return available AI models for the given type ('llm' or 'reasoning') from SDK, or []."""
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
    """Fallback: GET /configurationManager/ai-models/available/{modelType} when SDK does not return models."""
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
    """
    Build the `models` payload for agent create: one LLM and optionally a reasoning model.
    Prefers GPT-4o when available; otherwise uses SDK/API default. Returns list of dicts with
    modelKey, provider, modelName, isReasoning.
    """
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


def create_agent(pipeshub: Any, server_url: str, token: str) -> str:
    """Create a new agent via API and return its agent_key. Does not reuse existing agents by name."""
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


def main() -> None:
    server_url = os.getenv("PIPESHUB_SERVER_URL", DEFAULT_SERVER_URL).strip() or DEFAULT_SERVER_URL
    token = get_bearer_token(server_url)
    with get_pipeshub_client(server_url, token) as pipeshub:
        agent_key = create_agent(pipeshub, server_url, token)
    logger.info("Agent key (use this for chat or API calls): " + str(agent_key))


if __name__ == "__main__":
    main()
