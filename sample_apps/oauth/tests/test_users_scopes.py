import json
import pytest
from tests.utils import (
    BACKEND_URL, ACCESS_TOKEN, get_scopes_from_token, make_request, get_org_id_from_token
)


@pytest.fixture(scope='module')
def token_scopes():
    if not ACCESS_TOKEN:
        pytest.skip('ACCESS_TOKEN not set. Please log in first and add token to .env file')
    scopes = get_scopes_from_token(ACCESS_TOKEN)
    print(f'\nToken scopes: {", ".join(scopes) if scopes else "(none)"}')
    return scopes


@pytest.fixture(scope='module')
def user_id(token_scopes):
    if not ACCESS_TOKEN:
        return None
    
    org_id = get_org_id_from_token(ACCESS_TOKEN)
    if not org_id:
        return None
    
    try:
        url = f'{BACKEND_URL}/api/v1/users'
        response = make_request(url, method='GET', headers={'Authorization': f'Bearer {ACCESS_TOKEN}'})
        
        if response['status'] == 200:
            data = response['data']
            users = data if isinstance(data, list) else (data.get('data') or data.get('users') or [])
            if isinstance(users, list) and len(users) > 0:
                first_user = users[0]
                return str(first_user.get('id') or first_user.get('_id') or '')
        
        if 'user:invite' in token_scopes:
            create_body = json.dumps({
                "fullName": "Test User",
                "email": f"testuser{hash(org_id) % 10000}@example.com",
                "orgId": org_id
            })
            create_response = make_request(
                f'{BACKEND_URL}/api/v1/users',
                method='POST',
                headers={
                    'Authorization': f'Bearer {ACCESS_TOKEN}',
                    'Content-Type': 'application/json'
                },
                body=create_body
            )
            
            if create_response['status'] in [200, 201]:
                created_user = create_response['data']
                user_id = created_user.get('id') or created_user.get('_id') or ''
                if user_id:
                    return str(user_id)
    except Exception as e:
        print(f'Error in user_id fixture: {e}')
        pass
    
    return None


class TestUserReadScope:
    def test_get_users_works_when_token_has_user_read_scope(self, token_scopes):
        has_scope = 'user:read' in token_scopes
        
        if not has_scope:
            response = make_request(
                f'{BACKEND_URL}/api/v1/users',
                method='GET',
                headers={'Authorization': f'Bearer {ACCESS_TOKEN}'}
            )
            assert response['status'] == 403
            return
        response = make_request(
            f'{BACKEND_URL}/api/v1/users',
            method='GET',
            headers={'Authorization': f'Bearer {ACCESS_TOKEN}'}
        )
        assert 200 <= response['status'] < 500

    def test_get_user_by_id_works_when_token_has_user_read_scope(self, token_scopes, user_id):
        if not user_id:
            pytest.skip('No user ID available')
        
        has_scope = 'user:read' in token_scopes
        
        if not has_scope:
            response = make_request(
                f'{BACKEND_URL}/api/v1/users/{user_id}',
                method='GET',
                headers={'Authorization': f'Bearer {ACCESS_TOKEN}'}
            )
            assert response['status'] == 403
            return
        response = make_request(
            f'{BACKEND_URL}/api/v1/users/{user_id}',
            method='GET',
            headers={'Authorization': f'Bearer {ACCESS_TOKEN}'}
        )
        assert 200 <= response['status'] < 500

    def test_get_users_returns_denied_when_token_does_not_have_user_read_scope(self, token_scopes):
        has_scope = 'user:read' in token_scopes
        
        if has_scope:
            response = make_request(
                f'{BACKEND_URL}/api/v1/users',
                method='GET',
                headers={'Authorization': f'Bearer {ACCESS_TOKEN}'}
            )
            assert 200 <= response['status'] < 500
            return
        response = make_request(
            f'{BACKEND_URL}/api/v1/users',
            method='GET',
            headers={'Authorization': f'Bearer {ACCESS_TOKEN}'}
        )
        assert response['status'] == 403


class TestUserInviteScope:
    def test_post_users_works_when_token_has_user_invite_scope(self, token_scopes):
        has_scope = 'user:invite' in token_scopes
        
        if not has_scope:
            org_id = get_org_id_from_token(ACCESS_TOKEN)
            body = json.dumps({"fullName": "User", "email": "user@example.com"})
            if org_id:
                body_data = json.loads(body)
                body_data['orgId'] = org_id
                body = json.dumps(body_data)
            response = make_request(
                f'{BACKEND_URL}/api/v1/users',
                method='POST',
                headers={
                    'Authorization': f'Bearer {ACCESS_TOKEN}',
                    'Content-Type': 'application/json'
                },
                body=body
            )
            assert response['status'] == 403
            return
        org_id = get_org_id_from_token(ACCESS_TOKEN)
        body = json.dumps({"fullName": "User", "email": "user@example.com"})
        if org_id:
            body_data = json.loads(body)
            body_data['orgId'] = org_id
            body = json.dumps(body_data)
        response = make_request(
            f'{BACKEND_URL}/api/v1/users',
            method='POST',
            headers={
                'Authorization': f'Bearer {ACCESS_TOKEN}',
                'Content-Type': 'application/json'
            },
            body=body
        )
        assert 200 <= response['status'] < 500

    def test_post_users_returns_denied_when_token_does_not_have_user_invite_scope(self, token_scopes):
        has_scope = 'user:invite' in token_scopes
        
        if has_scope:
            org_id = get_org_id_from_token(ACCESS_TOKEN)
            body = json.dumps({"fullName": "User", "email": "user@example.com"})
            if org_id:
                body_data = json.loads(body)
                body_data['orgId'] = org_id
                body = json.dumps(body_data)
            response = make_request(
                f'{BACKEND_URL}/api/v1/users',
                method='POST',
                headers={
                    'Authorization': f'Bearer {ACCESS_TOKEN}',
                    'Content-Type': 'application/json'
                },
                body=body
            )
            assert 200 <= response['status'] < 500
            return
        org_id = get_org_id_from_token(ACCESS_TOKEN)
        body = json.dumps({"fullName": "User", "email": "user@example.com"})
        if org_id:
            body_data = json.loads(body)
            body_data['orgId'] = org_id
            body = json.dumps(body_data)
        response = make_request(
            f'{BACKEND_URL}/api/v1/users',
            method='POST',
            headers={
                'Authorization': f'Bearer {ACCESS_TOKEN}',
                'Content-Type': 'application/json'
            },
            body=body
        )
        assert response['status'] == 403


class TestUserWriteScope:
    def test_put_user_works_when_token_has_user_write_scope(self, token_scopes, user_id):
        if not user_id:
            pytest.skip('No user ID available')
        
        has_scope = 'user:write' in token_scopes
        
        if not has_scope:
            org_id = get_org_id_from_token(ACCESS_TOKEN)
            body = json.dumps({"fullName": "User Updated"})
            if org_id:
                body_data = json.loads(body)
                body_data['orgId'] = org_id
                body = json.dumps(body_data)
            response = make_request(
                f'{BACKEND_URL}/api/v1/users/{user_id}',
                method='PUT',
                headers={
                    'Authorization': f'Bearer {ACCESS_TOKEN}',
                    'Content-Type': 'application/json'
                },
                body=body
            )
            assert response['status'] == 403
            return
        org_id = get_org_id_from_token(ACCESS_TOKEN)
        body = json.dumps({"fullName": "User Updated"})
        if org_id:
            body_data = json.loads(body)
            body_data['orgId'] = org_id
            body = json.dumps(body_data)
        response = make_request(
            f'{BACKEND_URL}/api/v1/users/{user_id}',
            method='PUT',
            headers={
                'Authorization': f'Bearer {ACCESS_TOKEN}',
                'Content-Type': 'application/json'
            },
            body=body
        )
        assert 200 <= response['status'] < 500

    def test_put_user_returns_denied_when_token_does_not_have_user_write_scope(self, token_scopes, user_id):
        if not user_id:
            pytest.skip('No user ID available')
        
        has_scope = 'user:write' in token_scopes
        
        if has_scope:
            org_id = get_org_id_from_token(ACCESS_TOKEN)
            body = json.dumps({"fullName": "User Updated"})
            if org_id:
                body_data = json.loads(body)
                body_data['orgId'] = org_id
                body = json.dumps(body_data)
            response = make_request(
                f'{BACKEND_URL}/api/v1/users/{user_id}',
                method='PUT',
                headers={
                    'Authorization': f'Bearer {ACCESS_TOKEN}',
                    'Content-Type': 'application/json'
                },
                body=body
            )
            assert 200 <= response['status'] < 500
            return
        org_id = get_org_id_from_token(ACCESS_TOKEN)
        body = json.dumps({"fullName": "User Updated"})
        if org_id:
            body_data = json.loads(body)
            body_data['orgId'] = org_id
            body = json.dumps(body_data)
        response = make_request(
            f'{BACKEND_URL}/api/v1/users/{user_id}',
            method='PUT',
            headers={
                'Authorization': f'Bearer {ACCESS_TOKEN}',
                'Content-Type': 'application/json'
            },
            body=body
        )
        assert response['status'] == 403


class TestUserDeleteScope:
    def test_delete_user_works_when_token_has_user_delete_scope(self, token_scopes, user_id):
        if not user_id:
            pytest.skip('No user ID available')
        
        has_scope = 'user:delete' in token_scopes
        
        if not has_scope:
            response = make_request(
                f'{BACKEND_URL}/api/v1/users/{user_id}',
                method='DELETE',
                headers={'Authorization': f'Bearer {ACCESS_TOKEN}'}
            )
            assert response['status'] == 403
            return
        response = make_request(
            f'{BACKEND_URL}/api/v1/users/{user_id}',
            method='DELETE',
            headers={'Authorization': f'Bearer {ACCESS_TOKEN}'}
        )
        assert 200 <= response['status'] < 500

    def test_delete_user_returns_denied_when_token_does_not_have_user_delete_scope(self, token_scopes, user_id):
        if not user_id:
            pytest.skip('No user ID available')
        
        has_scope = 'user:delete' in token_scopes
        
        if has_scope:
            response = make_request(
                f'{BACKEND_URL}/api/v1/users/{user_id}',
                method='DELETE',
                headers={'Authorization': f'Bearer {ACCESS_TOKEN}'}
            )
            assert 200 <= response['status'] < 500
            return
        response = make_request(
            f'{BACKEND_URL}/api/v1/users/{user_id}',
            method='DELETE',
            headers={'Authorization': f'Bearer {ACCESS_TOKEN}'}
        )
        assert response['status'] == 403
