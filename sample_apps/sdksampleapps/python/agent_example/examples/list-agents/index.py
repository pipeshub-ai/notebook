"""
List-agents example: fetch and print all agents for the authenticated user.

Calls GET /agents with the token from get_bearer_token() (env or OAuth).
The API may return a list or a wrapper object (e.g. { "data": [...] }); we normalize to a list.

Run from agent_example directory:
  python examples/list-agents/index.py
  python main.py list-agents
"""
import os
import sys

_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, _root)

import requests
from dotenv import load_dotenv

from src.auth import get_bearer_token
from src.logger import logger

load_dotenv()

DEFAULT_SERVER_URL = "https://app.pipeshub.com/api/v1"


def list_agents_via_api(server_url: str, token: str) -> list:
    """
    GET /agents and return a list of agent objects.

    Handles both response shapes: raw list or wrapped (e.g. { "data": [...] }).
    Raises RuntimeError on HTTP error.
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
    if isinstance(data, list):
        return data
    for key in ("data", "agents", "result"):
        if isinstance(data.get(key), list):
            return data[key]
    return []


def main() -> None:
    server_url = os.getenv("PIPESHUB_SERVER_URL", DEFAULT_SERVER_URL).strip() or DEFAULT_SERVER_URL
    token = get_bearer_token(server_url)
    logger.info("Listing agents...")
    agents = list_agents_via_api(server_url, token)
    logger.json("Agents", agents if agents else [])


if __name__ == "__main__":
    main()
