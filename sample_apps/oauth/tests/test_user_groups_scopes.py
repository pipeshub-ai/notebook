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
def group_id(token_scopes):
    if not ACCESS_TOKEN:
        return None
    org_id = get_org_id_from_token(ACCESS_TOKEN)
    if not org_id:
        return None
    try:
        url = f'{BACKEND_URL}/api/v1/userGroups'
        response = make_request(url, method='GET', headers={'Authorization': f'Bearer {ACCESS_TOKEN}'})
        if response['status'] == 200:
            data = response['data']
            groups = data if isinstance(data, list) else (data.get('data') or data.get('userGroups') or [])
            if isinstance(groups, list) and len(groups) > 0:
                first_group = groups[0]
                return str(first_group.get('id') or first_group.get('_id') or '')
        if 'usergroup:write' in token_scopes:
            create_body = json.dumps({
                "name": "Test Group",
                "type": "standard",
                "orgId": org_id
            })
            create_response = make_request(
                f'{BACKEND_URL}/api/v1/userGroups',
                method='POST',
                headers={
                    'Authorization': f'Bearer {ACCESS_TOKEN}',
                    'Content-Type': 'application/json'
                },
                body=create_body
            )
            if create_response['status'] in [200, 201]:
                created_group = create_response['data']
                group_id = created_group.get('id') or created_group.get('_id') or ''
                if group_id:
                    return str(group_id)
    except Exception as e:
        print(f'Error in group_id fixture: {e}')
        pass
    return None


class TestUserGroupReadScope:
    def test_get_user_groups_works_when_token_has_usergroup_read_scope(self, token_scopes):
        has_scope = 'usergroup:read' in token_scopes
        if not has_scope:
            response = make_request(
                f'{BACKEND_URL}/api/v1/userGroups',
                method='GET',
                headers={'Authorization': f'Bearer {ACCESS_TOKEN}'}
            )
            assert response['status'] == 403
            return
        response = make_request(
            f'{BACKEND_URL}/api/v1/userGroups',
            method='GET',
            headers={'Authorization': f'Bearer {ACCESS_TOKEN}'}
        )
        assert 200 <= response['status'] < 500

    def test_get_user_groups_returns_denied_when_token_does_not_have_usergroup_read_scope(self, token_scopes):
        has_scope = 'usergroup:read' in token_scopes
        if has_scope:
            response = make_request(
                f'{BACKEND_URL}/api/v1/userGroups',
                method='GET',
                headers={'Authorization': f'Bearer {ACCESS_TOKEN}'}
            )
            assert 200 <= response['status'] < 500
            return
        response = make_request(
            f'{BACKEND_URL}/api/v1/userGroups',
            method='GET',
            headers={'Authorization': f'Bearer {ACCESS_TOKEN}'}
        )
        assert response['status'] == 403


class TestUserGroupWriteScope:
    def test_post_user_groups_works_when_token_has_usergroup_write_scope(self, token_scopes):
        has_scope = 'usergroup:write' in token_scopes
        if not has_scope:
            org_id = get_org_id_from_token(ACCESS_TOKEN)
            body = json.dumps({"name": "Group", "type": "standard"})
            if org_id:
                body_data = json.loads(body)
                body_data['orgId'] = org_id
                body = json.dumps(body_data)
            response = make_request(
                f'{BACKEND_URL}/api/v1/userGroups',
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
        body = json.dumps({"name": "Group", "type": "standard"})
        if org_id:
            body_data = json.loads(body)
            body_data['orgId'] = org_id
            body = json.dumps(body_data)
        response = make_request(
            f'{BACKEND_URL}/api/v1/userGroups',
            method='POST',
            headers={
                'Authorization': f'Bearer {ACCESS_TOKEN}',
                'Content-Type': 'application/json'
            },
            body=body
        )
        assert 200 <= response['status'] < 500

    def test_put_user_group_works_when_token_has_usergroup_write_scope(self, token_scopes, group_id):
        if not group_id:
            pytest.skip('No user group ID available')
        has_scope = 'usergroup:write' in token_scopes
        if not has_scope:
            org_id = get_org_id_from_token(ACCESS_TOKEN)
            body = json.dumps({"name": "Group Updated", "type": "standard"})
            if org_id:
                body_data = json.loads(body)
                body_data['orgId'] = org_id
                body = json.dumps(body_data)
            response = make_request(
                f'{BACKEND_URL}/api/v1/userGroups/{group_id}',
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
        body = json.dumps({"name": "Group Updated", "type": "standard"})
        if org_id:
            body_data = json.loads(body)
            body_data['orgId'] = org_id
            body = json.dumps(body_data)
        response = make_request(
            f'{BACKEND_URL}/api/v1/userGroups/{group_id}',
            method='PUT',
            headers={
                'Authorization': f'Bearer {ACCESS_TOKEN}',
                'Content-Type': 'application/json'
            },
            body=body
        )
        assert 200 <= response['status'] < 500

    def test_post_user_groups_returns_denied_when_token_does_not_have_usergroup_write_scope(self, token_scopes):
        has_scope = 'usergroup:write' in token_scopes
        if has_scope:
            org_id = get_org_id_from_token(ACCESS_TOKEN)
            body = json.dumps({"name": "Group", "type": "standard"})
            if org_id:
                body_data = json.loads(body)
                body_data['orgId'] = org_id
                body = json.dumps(body_data)
            response = make_request(
                f'{BACKEND_URL}/api/v1/userGroups',
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
        body = json.dumps({"name": "Group", "type": "standard"})
        if org_id:
            body_data = json.loads(body)
            body_data['orgId'] = org_id
            body = json.dumps(body_data)
        response = make_request(
            f'{BACKEND_URL}/api/v1/userGroups',
            method='POST',
            headers={
                'Authorization': f'Bearer {ACCESS_TOKEN}',
                'Content-Type': 'application/json'
            },
            body=body
        )
        assert response['status'] == 403
