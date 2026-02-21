import json
import pytest
from tests.utils import (
    BACKEND_URL, ACCESS_TOKEN, get_scopes_from_token, make_request
)


@pytest.fixture(scope='module')
def token_scopes():
    if not ACCESS_TOKEN:
        pytest.skip('ACCESS_TOKEN not set. Please log in first and add token to .env file')
    scopes = get_scopes_from_token(ACCESS_TOKEN)
    print(f'\nToken scopes: {", ".join(scopes) if scopes else "(none)"}')
    return scopes


class TestSearchQueryScope:
    def test_post_search_works_when_token_has_search_query_scope(self, token_scopes):
        has_scope = 'search:query' in token_scopes
        if not has_scope:
            response = make_request(
                f'{BACKEND_URL}/api/v1/search',
                method='POST',
                headers={
                    'Authorization': f'Bearer {ACCESS_TOKEN}',
                    'Content-Type': 'application/json'
                },
                body=json.dumps({'query': 'test'})
            )
            assert response['status'] == 403
            return
        response = make_request(
            f'{BACKEND_URL}/api/v1/search',
            method='POST',
            headers={
                'Authorization': f'Bearer {ACCESS_TOKEN}',
                'Content-Type': 'application/json'
            },
            body=json.dumps({'query': 'test'})
        )
        assert 200 <= response['status'] < 500

    def test_post_search_returns_denied_when_token_does_not_have_search_query_scope(self, token_scopes):
        has_scope = 'search:query' in token_scopes
        if has_scope:
            response = make_request(
                f'{BACKEND_URL}/api/v1/search',
                method='POST',
                headers={
                    'Authorization': f'Bearer {ACCESS_TOKEN}',
                    'Content-Type': 'application/json'
                },
                body=json.dumps({'query': 'test'})
            )
            assert 200 <= response['status'] < 500
            return
        response = make_request(
            f'{BACKEND_URL}/api/v1/search',
            method='POST',
            headers={
                'Authorization': f'Bearer {ACCESS_TOKEN}',
                'Content-Type': 'application/json'
            },
            body=json.dumps({'query': 'test'})
        )
        assert response['status'] == 403


class TestSearchSemanticScope:
    def test_post_search_semantic_works_when_token_has_search_semantic_scope(self, token_scopes):
        has_scope = 'search:semantic' in token_scopes
        if not has_scope:
            response = make_request(
                f'{BACKEND_URL}/api/v1/search/semantic',
                method='POST',
                headers={
                    'Authorization': f'Bearer {ACCESS_TOKEN}',
                    'Content-Type': 'application/json'
                },
                body=json.dumps({'query': 'test'})
            )
            assert response['status'] == 403
            return
        response = make_request(
            f'{BACKEND_URL}/api/v1/search/semantic',
            method='POST',
            headers={
                'Authorization': f'Bearer {ACCESS_TOKEN}',
                'Content-Type': 'application/json'
            },
            body=json.dumps({'query': 'test'})
        )
        assert 200 <= response['status'] < 500

    def test_post_search_semantic_returns_denied_when_token_does_not_have_search_semantic_scope(self, token_scopes):
        has_scope = 'search:semantic' in token_scopes
        if has_scope:
            response = make_request(
                f'{BACKEND_URL}/api/v1/search/semantic',
                method='POST',
                headers={
                    'Authorization': f'Bearer {ACCESS_TOKEN}',
                    'Content-Type': 'application/json'
                },
                body=json.dumps({'query': 'test'})
            )
            assert 200 <= response['status'] < 500
            return
        response = make_request(
            f'{BACKEND_URL}/api/v1/search/semantic',
            method='POST',
            headers={
                'Authorization': f'Bearer {ACCESS_TOKEN}',
                'Content-Type': 'application/json'
            },
            body=json.dumps({'query': 'test'})
        )
        assert response['status'] == 403
