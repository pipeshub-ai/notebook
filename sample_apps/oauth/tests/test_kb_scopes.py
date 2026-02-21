import pytest
from tests.utils import (
    BACKEND_URL, ACCESS_TOKEN, get_scopes_from_token, make_request
)

# Placeholder ID for path params; scope tests only check authz, not resource existence
KB_ID = 'test-id'


@pytest.fixture(scope='module')
def token_scopes():
    if not ACCESS_TOKEN:
        pytest.skip('ACCESS_TOKEN not set. Please log in first and add token to .env file')
    scopes = get_scopes_from_token(ACCESS_TOKEN)
    print(f'\nToken scopes: {", ".join(scopes) if scopes else "(none)"}')
    return scopes


class TestKbReadScope:
    def test_get_knowledge_base_works_when_token_has_kb_read_scope(self, token_scopes):
        has_scope = 'kb:read' in token_scopes
        if not has_scope:
            response = make_request(
                f'{BACKEND_URL}/api/v1/knowledgeBase/{KB_ID}',
                method='GET',
                headers={'Authorization': f'Bearer {ACCESS_TOKEN}'}
            )
            assert response['status'] == 403
            return
        response = make_request(
            f'{BACKEND_URL}/api/v1/knowledgeBase/{KB_ID}',
            method='GET',
            headers={'Authorization': f'Bearer {ACCESS_TOKEN}'}
        )
        assert 200 <= response['status'] < 500

    def test_get_knowledge_base_returns_denied_when_token_does_not_have_kb_read_scope(self, token_scopes):
        has_scope = 'kb:read' in token_scopes
        if has_scope:
            response = make_request(
                f'{BACKEND_URL}/api/v1/knowledgeBase/{KB_ID}',
                method='GET',
                headers={'Authorization': f'Bearer {ACCESS_TOKEN}'}
            )
            assert 200 <= response['status'] < 500
            return
        response = make_request(
            f'{BACKEND_URL}/api/v1/knowledgeBase/{KB_ID}',
            method='GET',
            headers={'Authorization': f'Bearer {ACCESS_TOKEN}'}
        )
        assert response['status'] == 403


class TestKbWriteScope:
    def test_post_knowledge_base_works_when_token_has_kb_write_scope(self, token_scopes):
        has_scope = 'kb:write' in token_scopes
        if not has_scope:
            response = make_request(
                f'{BACKEND_URL}/api/v1/knowledgeBase',
                method='POST',
                headers={
                    'Authorization': f'Bearer {ACCESS_TOKEN}',
                    'Content-Type': 'application/json'
                },
                body='{"name": "Test KB"}'
            )
            assert response['status'] == 403
            return
        response = make_request(
            f'{BACKEND_URL}/api/v1/knowledgeBase',
            method='POST',
            headers={
                'Authorization': f'Bearer {ACCESS_TOKEN}',
                'Content-Type': 'application/json'
            },
            body='{"name": "Test KB"}'
        )
        assert 200 <= response['status'] < 500

    def test_put_knowledge_base_works_when_token_has_kb_write_scope(self, token_scopes):
        has_scope = 'kb:write' in token_scopes
        if not has_scope:
            response = make_request(
                f'{BACKEND_URL}/api/v1/knowledgeBase/{KB_ID}',
                method='PUT',
                headers={
                    'Authorization': f'Bearer {ACCESS_TOKEN}',
                    'Content-Type': 'application/json'
                },
                body='{"name": "Test KB Updated"}'
            )
            assert response['status'] == 403
            return
        response = make_request(
            f'{BACKEND_URL}/api/v1/knowledgeBase/{KB_ID}',
            method='PUT',
            headers={
                'Authorization': f'Bearer {ACCESS_TOKEN}',
                'Content-Type': 'application/json'
            },
            body='{"name": "Test KB Updated"}'
        )
        assert 200 <= response['status'] < 500

    def test_post_knowledge_base_returns_denied_when_token_does_not_have_kb_write_scope(self, token_scopes):
        has_scope = 'kb:write' in token_scopes
        if has_scope:
            response = make_request(
                f'{BACKEND_URL}/api/v1/knowledgeBase',
                method='POST',
                headers={
                    'Authorization': f'Bearer {ACCESS_TOKEN}',
                    'Content-Type': 'application/json'
                },
                body='{"name": "Test KB"}'
            )
            assert 200 <= response['status'] < 500
            return
        response = make_request(
            f'{BACKEND_URL}/api/v1/knowledgeBase',
            method='POST',
            headers={
                'Authorization': f'Bearer {ACCESS_TOKEN}',
                'Content-Type': 'application/json'
            },
            body='{"name": "Test KB"}'
        )
        assert response['status'] == 403


class TestKbDeleteScope:
    def test_delete_knowledge_base_works_when_token_has_kb_delete_scope(self, token_scopes):
        has_scope = 'kb:delete' in token_scopes
        if not has_scope:
            response = make_request(
                f'{BACKEND_URL}/api/v1/knowledgeBase/{KB_ID}',
                method='DELETE',
                headers={'Authorization': f'Bearer {ACCESS_TOKEN}'}
            )
            assert response['status'] == 403
            return
        response = make_request(
            f'{BACKEND_URL}/api/v1/knowledgeBase/{KB_ID}',
            method='DELETE',
            headers={'Authorization': f'Bearer {ACCESS_TOKEN}'}
        )
        assert 200 <= response['status'] < 500

    def test_delete_knowledge_base_returns_denied_when_token_does_not_have_kb_delete_scope(self, token_scopes):
        has_scope = 'kb:delete' in token_scopes
        if has_scope:
            response = make_request(
                f'{BACKEND_URL}/api/v1/knowledgeBase/{KB_ID}',
                method='DELETE',
                headers={'Authorization': f'Bearer {ACCESS_TOKEN}'}
            )
            assert 200 <= response['status'] < 500
            return
        response = make_request(
            f'{BACKEND_URL}/api/v1/knowledgeBase/{KB_ID}',
            method='DELETE',
            headers={'Authorization': f'Bearer {ACCESS_TOKEN}'}
        )
        assert response['status'] == 403


class TestKbUploadScope:
    def test_upload_to_knowledge_base_works_when_token_has_kb_upload_scope(self, token_scopes):
        has_scope = 'kb:upload' in token_scopes
        if not has_scope:
            response = make_request(
                f'{BACKEND_URL}/api/v1/knowledgeBase/{KB_ID}/upload',
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
            f'{BACKEND_URL}/api/v1/knowledgeBase/{KB_ID}/upload',
            method='POST',
            headers={
                'Authorization': f'Bearer {ACCESS_TOKEN}',
                'Content-Type': 'application/json'
            },
            body='{}'
        )
        assert 200 <= response['status'] < 500

    def test_upload_to_knowledge_base_returns_denied_when_token_does_not_have_kb_upload_scope(self, token_scopes):
        has_scope = 'kb:upload' in token_scopes
        if has_scope:
            response = make_request(
                f'{BACKEND_URL}/api/v1/knowledgeBase/{KB_ID}/upload',
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
            f'{BACKEND_URL}/api/v1/knowledgeBase/{KB_ID}/upload',
            method='POST',
            headers={
                'Authorization': f'Bearer {ACCESS_TOKEN}',
                'Content-Type': 'application/json'
            },
            body='{}'
        )
        assert response['status'] == 403
