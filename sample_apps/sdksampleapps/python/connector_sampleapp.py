import os
import json
from dotenv import load_dotenv
from pipeshub_sdk import Pipeshub, models

load_dotenv()


def get_oauth_access_token(server_url: str, bearer_auth: str, client_id: str, client_secret: str) -> str:
    """Get an OAuth access token using client_id and client_secret."""
    with Pipeshub(
        security=models.Security(bearer_auth=bearer_auth),
        server_url=server_url,
    ) as pipeshub:
        res = pipeshub.o_auth_provider.oauth_token(
            grant_type="client_credentials",
            client_id=client_id,
            client_secret=client_secret,
        )
        print("OAuth Token Response:")
        print(f"  Access Token: {res.access_token[:20]}..." if res.access_token else "  No access token")
        print(f"  Token Type: {res.token_type}")
        print(f"  Expires In: {res.expires_in}s")
        if res.refresh_token:
            print(f"  Refresh Token: {res.refresh_token[:20]}...")
        if res.scope:
            print(f"  Scope: {res.scope}")
        return res.access_token


def list_connector_instances(pipeshub: Pipeshub):
    """List all configured connector instances."""
    print("\n--- Connector Instances ---")
    res = pipeshub.connector_instances.list_connector_instances(scope="team", page=1, limit=20)
    print(json.dumps(res, indent=2, default=str))


def get_connector_registry(pipeshub: Pipeshub):
    """List available connector types from the registry."""
    print("\n--- Connector Registry ---")
    res = pipeshub.connector_registry.get_connector_registry(scope="team", page=1, limit=20)
    print(json.dumps(res, indent=2, default=str))


def list_oauth_apps(pipeshub: Pipeshub):
    """List all OAuth apps registered for the organization."""
    print("\n--- OAuth Apps ---")
    res = pipeshub.o_auth_apps.list_o_auth_apps(page=1, limit=20)
    print(json.dumps(res, indent=2, default=str))


def main():
    server_url = os.getenv("PIPESHUB_SERVER_URL", "http://localhost:3000/api/v1")
    bearer_auth = os.getenv("PIPESHUB_BEARER_AUTH", "")
    client_id = os.getenv("PIPESHUB_CLIENT_ID", "")
    client_secret = os.getenv("PIPESHUB_CLIENT_SECRET", "")

    if not bearer_auth:
        raise ValueError("PIPESHUB_BEARER_AUTH environment variable is required")
    if not client_id or not client_secret:
        raise ValueError("PIPESHUB_CLIENT_ID and PIPESHUB_CLIENT_SECRET environment variables are required")

    # Step 1: Get OAuth access token using client credentials
    print("=== Step 1: Getting OAuth Access Token ===")
    access_token = get_oauth_access_token(server_url, bearer_auth, client_id, client_secret)

    # Step 2: Initialize SDK with the OAuth access token
    print("\n=== Step 2: Using OAuth Token for API Calls ===")
    with Pipeshub(
        security=models.Security(bearer_auth=access_token),
        server_url=server_url,
    ) as pipeshub:
        list_oauth_apps(pipeshub)
        list_connector_instances(pipeshub)
        get_connector_registry(pipeshub)


if __name__ == "__main__":
    main()
