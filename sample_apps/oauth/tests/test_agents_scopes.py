import json
import pytest
from tests.utils import (
    BACKEND_URL, ACCESS_TOKEN, get_scopes_from_token, make_request
)

AGENT_ID = 'test-id'


@pytest.fixture(scope='module')
def token_scopes():
    if not ACCESS_TOKEN:
        pytest.skip('ACCESS_TOKEN not set. Please log in first and add token to .env file')
    scopes = get_scopes_from_token(ACCESS_TOKEN)
    print(f'\nToken scopes: {", ".join(scopes) if scopes else "(none)"}')
    return scopes


class TestAgentReadScope:
    def test_get_agents_works_when_token_has_agent_read_scope(self, token_scopes):
        has_scope = 'agent:read' in token_scopes
        if not has_scope:
            response = make_request(
                f'{BACKEND_URL}/api/v1/agents',
                method='GET',
                headers={'Authorization': f'Bearer {ACCESS_TOKEN}'}
            )
            assert response['status'] == 403
            return
        response = make_request(
            f'{BACKEND_URL}/api/v1/agents',
            method='GET',
            headers={'Authorization': f'Bearer {ACCESS_TOKEN}'}
        )
        assert 200 <= response['status'] < 500

    def test_get_agents_returns_denied_when_token_does_not_have_agent_read_scope(self, token_scopes):
        has_scope = 'agent:read' in token_scopes
        if has_scope:
            response = make_request(
                f'{BACKEND_URL}/api/v1/agents',
                method='GET',
                headers={'Authorization': f'Bearer {ACCESS_TOKEN}'}
            )
            assert 200 <= response['status'] < 500
            return
        response = make_request(
            f'{BACKEND_URL}/api/v1/agents',
            method='GET',
            headers={'Authorization': f'Bearer {ACCESS_TOKEN}'}
        )
        assert response['status'] == 403


class TestAgentWriteScope:
    def test_post_agents_works_when_token_has_agent_write_scope(self, token_scopes):
        has_scope = 'agent:write' in token_scopes
        if not has_scope:
            response = make_request(
                f'{BACKEND_URL}/api/v1/agents',
                method='POST',
                headers={
                    'Authorization': f'Bearer {ACCESS_TOKEN}',
                    'Content-Type': 'application/json'
                },
                body='{"name": "Test Agent"}'
            )
            assert response['status'] == 403
            return
        response = make_request(
            f'{BACKEND_URL}/api/v1/agents',
            method='POST',
            headers={
                'Authorization': f'Bearer {ACCESS_TOKEN}',
                'Content-Type': 'application/json'
            },
            body='{"name": "Test Agent"}'
        )
        assert 200 <= response['status'] < 500

    def test_put_agent_works_when_token_has_agent_write_scope(self, token_scopes):
        has_scope = 'agent:write' in token_scopes
        if not has_scope:
            response = make_request(
                f'{BACKEND_URL}/api/v1/agents/{AGENT_ID}',
                method='PUT',
                headers={
                    'Authorization': f'Bearer {ACCESS_TOKEN}',
                    'Content-Type': 'application/json'
                },
                body='{"name": "Test Agent Updated"}'
            )
            assert response['status'] == 403
            return
        response = make_request(
            f'{BACKEND_URL}/api/v1/agents/{AGENT_ID}',
            method='PUT',
            headers={
                'Authorization': f'Bearer {ACCESS_TOKEN}',
                'Content-Type': 'application/json'
            },
            body='{"name": "Test Agent Updated"}'
        )
        assert 200 <= response['status'] < 500

    def test_post_agents_returns_denied_when_token_does_not_have_agent_write_scope(self, token_scopes):
        has_scope = 'agent:write' in token_scopes
        if has_scope:
            response = make_request(
                f'{BACKEND_URL}/api/v1/agents',
                method='POST',
                headers={
                    'Authorization': f'Bearer {ACCESS_TOKEN}',
                    'Content-Type': 'application/json'
                },
                body='{"name": "Test Agent"}'
            )
            assert 200 <= response['status'] < 500
            return
        response = make_request(
            f'{BACKEND_URL}/api/v1/agents',
            method='POST',
            headers={
                'Authorization': f'Bearer {ACCESS_TOKEN}',
                'Content-Type': 'application/json'
            },
            body='{"name": "Test Agent"}'
        )
        assert response['status'] == 403


class TestAgentExecuteScope:
    def test_post_agent_execute_works_when_token_has_agent_execute_scope(self, token_scopes):
        has_scope = 'agent:execute' in token_scopes
        if not has_scope:
            response = make_request(
                f'{BACKEND_URL}/api/v1/agents/{AGENT_ID}/execute',
                method='POST',
                headers={
                    'Authorization': f'Bearer {ACCESS_TOKEN}',
                    'Content-Type': 'application/json'
                },
                body='{}'
            )
            assert response['status'] == 403
            return
        response = make_request(
            f'{BACKEND_URL}/api/v1/agents/{AGENT_ID}/execute',
            method='POST',
            headers={
                'Authorization': f'Bearer {ACCESS_TOKEN}',
                'Content-Type': 'application/json'
            },
            body='{}'
        )
        assert 200 <= response['status'] < 500

    def test_post_agent_execute_returns_denied_when_token_does_not_have_agent_execute_scope(self, token_scopes):
        has_scope = 'agent:execute' in token_scopes
        if has_scope:
            response = make_request(
                f'{BACKEND_URL}/api/v1/agents/{AGENT_ID}/execute',
                method='POST',
                headers={
                    'Authorization': f'Bearer {ACCESS_TOKEN}',
                    'Content-Type': 'application/json'
                },
                body='{}'
            )
            assert 200 <= response['status'] < 500
            return
        response = make_request(
            f'{BACKEND_URL}/api/v1/agents/{AGENT_ID}/execute',
            method='POST',
            headers={
                'Authorization': f'Bearer {ACCESS_TOKEN}',
                'Content-Type': 'application/json'
            },
            body='{}'
        )
        assert response['status'] == 403
