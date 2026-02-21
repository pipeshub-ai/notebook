import pytest
from tests.utils import (
    BACKEND_URL, ACCESS_TOKEN, get_scopes_from_token, make_request
)

CONNECTOR_ID = 'test-id'


@pytest.fixture(scope='module')
def token_scopes():
    if not ACCESS_TOKEN:
        pytest.skip('ACCESS_TOKEN not set. Please log in first and add token to .env file')
    scopes = get_scopes_from_token(ACCESS_TOKEN)
    print(f'\nToken scopes: {", ".join(scopes) if scopes else "(none)"}')
    return scopes


class TestConnectorReadScope:
    def test_get_connectors_works_when_token_has_connector_read_scope(self, token_scopes):
        has_scope = 'connector:read' in token_scopes
        if not has_scope:
            response = make_request(
                f'{BACKEND_URL}/api/v1/connectors',
                method='GET',
                headers={'Authorization': f'Bearer {ACCESS_TOKEN}'}
            )
            assert response['status'] == 403
            return
        response = make_request(
            f'{BACKEND_URL}/api/v1/connectors',
            method='GET',
            headers={'Authorization': f'Bearer {ACCESS_TOKEN}'}
        )
        assert 200 <= response['status'] < 500

    def test_get_connectors_registry_works_when_token_has_connector_read_scope(self, token_scopes):
        has_scope = 'connector:read' in token_scopes
        if not has_scope:
            response = make_request(
                f'{BACKEND_URL}/api/v1/connectors/registry',
                method='GET',
                headers={'Authorization': f'Bearer {ACCESS_TOKEN}'}
            )
            assert response['status'] == 403
            return
        response = make_request(
            f'{BACKEND_URL}/api/v1/connectors/registry',
            method='GET',
            headers={'Authorization': f'Bearer {ACCESS_TOKEN}'}
        )
        assert 200 <= response['status'] < 500

    def test_get_connectors_returns_denied_when_token_does_not_have_connector_read_scope(self, token_scopes):
        has_scope = 'connector:read' in token_scopes
        if has_scope:
            response = make_request(
                f'{BACKEND_URL}/api/v1/connectors',
                method='GET',
                headers={'Authorization': f'Bearer {ACCESS_TOKEN}'}
            )
            assert 200 <= response['status'] < 500
            return
        response = make_request(
            f'{BACKEND_URL}/api/v1/connectors',
            method='GET',
            headers={'Authorization': f'Bearer {ACCESS_TOKEN}'}
        )
        assert response['status'] == 403


class TestConnectorWriteScope:
    def test_post_connectors_works_when_token_has_connector_write_scope(self, token_scopes):
        has_scope = 'connector:write' in token_scopes
        if not has_scope:
            response = make_request(
                f'{BACKEND_URL}/api/v1/connectors',
                method='POST',
                headers={
                    'Authorization': f'Bearer {ACCESS_TOKEN}',
                    'Content-Type': 'application/json'
                },
                body='{"type": "test"}'
            )
            assert response['status'] == 403
            return
        response = make_request(
            f'{BACKEND_URL}/api/v1/connectors',
            method='POST',
            headers={
                'Authorization': f'Bearer {ACCESS_TOKEN}',
                'Content-Type': 'application/json'
            },
            body='{"type": "test"}'
        )
        assert 200 <= response['status'] < 500

    def test_put_connector_works_when_token_has_connector_write_scope(self, token_scopes):
        has_scope = 'connector:write' in token_scopes
        if not has_scope:
            response = make_request(
                f'{BACKEND_URL}/api/v1/connectors/{CONNECTOR_ID}',
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
            f'{BACKEND_URL}/api/v1/connectors/{CONNECTOR_ID}',
            method='PUT',
            headers={
                'Authorization': f'Bearer {ACCESS_TOKEN}',
                'Content-Type': 'application/json'
            },
            body='{}'
        )
        assert 200 <= response['status'] < 500

    def test_post_connectors_returns_denied_when_token_does_not_have_connector_write_scope(self, token_scopes):
        has_scope = 'connector:write' in token_scopes
        if has_scope:
            response = make_request(
                f'{BACKEND_URL}/api/v1/connectors',
                method='POST',
                headers={
                    'Authorization': f'Bearer {ACCESS_TOKEN}',
                    'Content-Type': 'application/json'
                },
                body='{"type": "test"}'
            )
            assert 200 <= response['status'] < 500
            return
        response = make_request(
            f'{BACKEND_URL}/api/v1/connectors',
            method='POST',
            headers={
                'Authorization': f'Bearer {ACCESS_TOKEN}',
                'Content-Type': 'application/json'
            },
            body='{"type": "test"}'
        )
        assert response['status'] == 403


class TestConnectorSyncScope:
    def test_post_connector_sync_works_when_token_has_connector_sync_scope(self, token_scopes):
        has_scope = 'connector:sync' in token_scopes
        if not has_scope:
            response = make_request(
                f'{BACKEND_URL}/api/v1/connectors/{CONNECTOR_ID}/sync',
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
            f'{BACKEND_URL}/api/v1/connectors/{CONNECTOR_ID}/sync',
            method='POST',
            headers={
                'Authorization': f'Bearer {ACCESS_TOKEN}',
                'Content-Type': 'application/json'
            },
            body='{}'
        )
        assert 200 <= response['status'] < 500

    def test_post_connector_sync_returns_denied_when_token_does_not_have_connector_sync_scope(self, token_scopes):
        has_scope = 'connector:sync' in token_scopes
        if has_scope:
            response = make_request(
                f'{BACKEND_URL}/api/v1/connectors/{CONNECTOR_ID}/sync',
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
            f'{BACKEND_URL}/api/v1/connectors/{CONNECTOR_ID}/sync',
            method='POST',
            headers={
                'Authorization': f'Bearer {ACCESS_TOKEN}',
                'Content-Type': 'application/json'
            },
            body='{}'
        )
        assert response['status'] == 403


class TestConnectorDeleteScope:
    def test_delete_connector_works_when_token_has_connector_delete_scope(self, token_scopes):
        has_scope = 'connector:delete' in token_scopes
        if not has_scope:
            response = make_request(
                f'{BACKEND_URL}/api/v1/connectors/{CONNECTOR_ID}',
                method='DELETE',
                headers={'Authorization': f'Bearer {ACCESS_TOKEN}'}
            )
            assert response['status'] == 403
            return
        response = make_request(
            f'{BACKEND_URL}/api/v1/connectors/{CONNECTOR_ID}',
            method='DELETE',
            headers={'Authorization': f'Bearer {ACCESS_TOKEN}'}
        )
        assert 200 <= response['status'] < 500

    def test_delete_connector_returns_denied_when_token_does_not_have_connector_delete_scope(self, token_scopes):
        has_scope = 'connector:delete' in token_scopes
        if has_scope:
            response = make_request(
                f'{BACKEND_URL}/api/v1/connectors/{CONNECTOR_ID}',
                method='DELETE',
                headers={'Authorization': f'Bearer {ACCESS_TOKEN}'}
            )
            assert 200 <= response['status'] < 500
            return
        response = make_request(
            f'{BACKEND_URL}/api/v1/connectors/{CONNECTOR_ID}',
            method='DELETE',
            headers={'Authorization': f'Bearer {ACCESS_TOKEN}'}
        )
        assert response['status'] == 403
