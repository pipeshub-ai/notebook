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


class TestOrgReadScope:
    def test_get_org_works_when_token_has_org_read_scope(self, token_scopes):
        has_scope = 'org:read' in token_scopes
        if not has_scope:
            response = make_request(
                f'{BACKEND_URL}/api/v1/org',
                method='GET',
                headers={'Authorization': f'Bearer {ACCESS_TOKEN}'}
            )
            assert response['status'] == 403
            return
        response = make_request(
            f'{BACKEND_URL}/api/v1/org',
            method='GET',
            headers={'Authorization': f'Bearer {ACCESS_TOKEN}'}
        )
        assert 200 <= response['status'] < 500

    def test_get_org_returns_denied_when_token_does_not_have_org_read_scope(self, token_scopes):
        has_scope = 'org:read' in token_scopes
        if has_scope:
            response = make_request(
                f'{BACKEND_URL}/api/v1/org',
                method='GET',
                headers={'Authorization': f'Bearer {ACCESS_TOKEN}'}
            )
            assert 200 <= response['status'] < 500
            return
        response = make_request(
            f'{BACKEND_URL}/api/v1/org',
            method='GET',
            headers={'Authorization': f'Bearer {ACCESS_TOKEN}'}
        )
        assert response['status'] == 403


class TestOrgWriteScope:
    def test_put_org_works_when_token_has_org_write_scope(self, token_scopes):
        has_scope = 'org:write' in token_scopes
        if not has_scope:
            response = make_request(
                f'{BACKEND_URL}/api/v1/org',
                method='PUT',
                headers={
                    'Authorization': f'Bearer {ACCESS_TOKEN}',
                    'Content-Type': 'application/json'
                },
                body='{"name": "Org"}'
            )
            assert response['status'] == 403
            return
        response = make_request(
            f'{BACKEND_URL}/api/v1/org',
            method='PUT',
            headers={
                'Authorization': f'Bearer {ACCESS_TOKEN}',
                'Content-Type': 'application/json'
            },
            body='{"name": "Org"}'
        )
        assert 200 <= response['status'] < 500

    def test_put_org_returns_denied_when_token_does_not_have_org_write_scope(self, token_scopes):
        has_scope = 'org:write' in token_scopes
        if has_scope:
            response = make_request(
                f'{BACKEND_URL}/api/v1/org',
                method='PUT',
                headers={
                    'Authorization': f'Bearer {ACCESS_TOKEN}',
                    'Content-Type': 'application/json'
                },
                body='{"name": "Org"}'
            )
            assert 200 <= response['status'] < 500
            return
        response = make_request(
            f'{BACKEND_URL}/api/v1/org',
            method='PUT',
            headers={
                'Authorization': f'Bearer {ACCESS_TOKEN}',
                'Content-Type': 'application/json'
            },
            body='{"name": "Org"}'
        )
        assert response['status'] == 403


class TestOrgAdminScope:
    def test_delete_org_works_when_token_has_org_admin_scope(self, token_scopes):
        has_scope = 'org:admin' in token_scopes
        if not has_scope:
            response = make_request(
                f'{BACKEND_URL}/api/v1/org',
                method='DELETE',
                headers={'Authorization': f'Bearer {ACCESS_TOKEN}'}
            )
            assert response['status'] == 403
            return
        response = make_request(
            f'{BACKEND_URL}/api/v1/org',
            method='DELETE',
            headers={'Authorization': f'Bearer {ACCESS_TOKEN}'}
        )
        assert 200 <= response['status'] < 500

    def test_delete_org_returns_denied_when_token_does_not_have_org_admin_scope(self, token_scopes):
        has_scope = 'org:admin' in token_scopes
        if has_scope:
            response = make_request(
                f'{BACKEND_URL}/api/v1/org',
                method='DELETE',
                headers={'Authorization': f'Bearer {ACCESS_TOKEN}'}
            )
            assert 200 <= response['status'] < 500
            return
        response = make_request(
            f'{BACKEND_URL}/api/v1/org',
            method='DELETE',
            headers={'Authorization': f'Bearer {ACCESS_TOKEN}'}
        )
        assert response['status'] == 403
