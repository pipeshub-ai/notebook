"""
Auth example: obtain a PipesHub Bearer token.

Uses shared get_bearer_token() from src.auth:
  - If PIPESHUB_BEARER_AUTH is set, that token is used.
  - Otherwise OAuth browser login (PIPESHUB_OAUTH_CLIENT_ID + PIPESHUB_OAUTH_CLIENT_SECRET);
    a browser tab opens for login, then the script receives the token via local callback.

Run from agent_example directory:
  python examples/auth/index.py
  python main.py auth
"""
import os
import sys

# Allow importing from project root (src.auth, src.logger)
_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, _root)

from dotenv import load_dotenv

from src.auth import get_bearer_token
from src.logger import logger

load_dotenv()

DEFAULT_SERVER_URL = "https://app.pipeshub.com/api/v1"


def main() -> None:
    server_url = os.getenv("PIPESHUB_SERVER_URL", DEFAULT_SERVER_URL).strip() or DEFAULT_SERVER_URL
    try:
        token = get_bearer_token(server_url)
    except RuntimeError as e:
        logger.error(str(e))
        sys.exit(1)
    # Log only a short prefix to avoid leaking the full token
    logger.info("Got bearer token", token[:20] + "..." if len(token) > 20 else token)


if __name__ == "__main__":
    main()
