import json
import pytest
from tests.utils import (
    BACKEND_URL, ACCESS_TOKEN, get_scopes_from_token, make_request
)

CONV_ID = 'test-id'


@pytest.fixture(scope='module')
def token_scopes():
    if not ACCESS_TOKEN:
        pytest.skip('ACCESS_TOKEN not set. Please log in first and add token to .env file')
    scopes = get_scopes_from_token(ACCESS_TOKEN)
    print(f'\nToken scopes: {", ".join(scopes) if scopes else "(none)"}')
    return scopes


class TestConversationReadScope:
    def test_get_conversations_works_when_token_has_conversation_read_scope(self, token_scopes):
        has_scope = 'conversation:read' in token_scopes
        if not has_scope:
            response = make_request(
                f'{BACKEND_URL}/api/v1/conversations',
                method='GET',
                headers={'Authorization': f'Bearer {ACCESS_TOKEN}'}
            )
            assert response['status'] == 403
            return
        response = make_request(
            f'{BACKEND_URL}/api/v1/conversations',
            method='GET',
            headers={'Authorization': f'Bearer {ACCESS_TOKEN}'}
        )
        assert 200 <= response['status'] < 500

    def test_get_conversations_archives_works_when_token_has_conversation_read_scope(self, token_scopes):
        has_scope = 'conversation:read' in token_scopes
        if not has_scope:
            response = make_request(
                f'{BACKEND_URL}/api/v1/conversations/show/archives',
                method='GET',
                headers={'Authorization': f'Bearer {ACCESS_TOKEN}'}
            )
            assert response['status'] == 403
            return
        response = make_request(
            f'{BACKEND_URL}/api/v1/conversations/show/archives',
            method='GET',
            headers={'Authorization': f'Bearer {ACCESS_TOKEN}'}
        )
        assert 200 <= response['status'] < 500

    def test_get_conversations_returns_denied_when_token_does_not_have_conversation_read_scope(self, token_scopes):
        has_scope = 'conversation:read' in token_scopes
        if has_scope:
            response = make_request(
                f'{BACKEND_URL}/api/v1/conversations',
                method='GET',
                headers={'Authorization': f'Bearer {ACCESS_TOKEN}'}
            )
            assert 200 <= response['status'] < 500
            return
        response = make_request(
            f'{BACKEND_URL}/api/v1/conversations',
            method='GET',
            headers={'Authorization': f'Bearer {ACCESS_TOKEN}'}
        )
        assert response['status'] == 403


class TestConversationWriteScope:
    def test_post_conversations_create_works_when_token_has_conversation_write_scope(self, token_scopes):
        has_scope = 'conversation:write' in token_scopes
        if not has_scope:
            response = make_request(
                f'{BACKEND_URL}/api/v1/conversations/create',
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
            f'{BACKEND_URL}/api/v1/conversations/create',
            method='POST',
            headers={
                'Authorization': f'Bearer {ACCESS_TOKEN}',
                'Content-Type': 'application/json'
            },
            body='{}'
        )
        assert 200 <= response['status'] < 500

    def test_put_conversation_works_when_token_has_conversation_write_scope(self, token_scopes):
        has_scope = 'conversation:write' in token_scopes
        if not has_scope:
            response = make_request(
                f'{BACKEND_URL}/api/v1/conversations/{CONV_ID}',
                method='PUT',
                headers={
                    'Authorization': f'Bearer {ACCESS_TOKEN}',
                    'Content-Type': 'application/json'
                },
                body='{}'
            )
            assert response['status'] == 403
            return
        response = make_request(
            f'{BACKEND_URL}/api/v1/conversations/{CONV_ID}',
            method='PUT',
            headers={
                'Authorization': f'Bearer {ACCESS_TOKEN}',
                'Content-Type': 'application/json'
            },
            body='{}'
        )
        assert 200 <= response['status'] < 500

    def test_post_conversations_create_returns_denied_when_token_does_not_have_conversation_write_scope(self, token_scopes):
        has_scope = 'conversation:write' in token_scopes
        if has_scope:
            response = make_request(
                f'{BACKEND_URL}/api/v1/conversations/create',
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
            f'{BACKEND_URL}/api/v1/conversations/create',
            method='POST',
            headers={
                'Authorization': f'Bearer {ACCESS_TOKEN}',
                'Content-Type': 'application/json'
            },
            body='{}'
        )
        assert response['status'] == 403


class TestConversationChatScope:
    def test_post_conversation_chat_works_when_token_has_conversation_chat_scope(self, token_scopes):
        has_scope = 'conversation:chat' in token_scopes
        if not has_scope:
            response = make_request(
                f'{BACKEND_URL}/api/v1/conversations/{CONV_ID}/chat',
                method='POST',
                headers={
                    'Authorization': f'Bearer {ACCESS_TOKEN}',
                    'Content-Type': 'application/json'
                },
                body=json.dumps({'message': 'hello'})
            )
            assert response['status'] == 403
            return
        response = make_request(
            f'{BACKEND_URL}/api/v1/conversations/{CONV_ID}/chat',
            method='POST',
            headers={
                'Authorization': f'Bearer {ACCESS_TOKEN}',
                'Content-Type': 'application/json'
            },
            body=json.dumps({'message': 'hello'})
        )
        assert 200 <= response['status'] < 500

    def test_post_conversation_chat_returns_denied_when_token_does_not_have_conversation_chat_scope(self, token_scopes):
        has_scope = 'conversation:chat' in token_scopes
        if has_scope:
            response = make_request(
                f'{BACKEND_URL}/api/v1/conversations/{CONV_ID}/chat',
                method='POST',
                headers={
                    'Authorization': f'Bearer {ACCESS_TOKEN}',
                    'Content-Type': 'application/json'
                },
                body=json.dumps({'message': 'hello'})
            )
            assert 200 <= response['status'] < 500
            return
        response = make_request(
            f'{BACKEND_URL}/api/v1/conversations/{CONV_ID}/chat',
            method='POST',
            headers={
                'Authorization': f'Bearer {ACCESS_TOKEN}',
                'Content-Type': 'application/json'
            },
            body=json.dumps({'message': 'hello'})
        )
        assert response['status'] == 403
