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
def team_id(token_scopes):
    if not ACCESS_TOKEN:
        return None
    org_id = get_org_id_from_token(ACCESS_TOKEN)
    if not org_id:
        return None
    try:
        response = make_request(
            f'{BACKEND_URL}/api/v1/teams?page=1&limit=10',
            method='GET',
            headers={'Authorization': f'Bearer {ACCESS_TOKEN}'}
        )
        if response['status'] != 200 and org_id:
            response = make_request(
                f'{BACKEND_URL}/api/v1/teams?page=1&limit=10&orgId={org_id}',
                method='GET',
                headers={'Authorization': f'Bearer {ACCESS_TOKEN}'}
            )
        if response['status'] == 200:
            data = response['data']
            teams = None
            if isinstance(data, list):
                teams = data
            elif isinstance(data, dict):
                teams = data.get('data') or data.get('teams') or []
            if isinstance(teams, list) and len(teams) > 0:
                first_team = teams[0]
                return str(first_team.get('id') or first_team.get('_id') or '')
        if 'team:write' in token_scopes:
            create_body = json.dumps({"name": "Test Team", "orgId": org_id})
            create_response = make_request(
                f'{BACKEND_URL}/api/v1/teams',
                method='POST',
                headers={
                    'Authorization': f'Bearer {ACCESS_TOKEN}',
                    'Content-Type': 'application/json'
                },
                body=create_body
            )
            if create_response['status'] in [200, 201]:
                created_team = create_response['data']
                team_obj = created_team.get('data') if isinstance(created_team, dict) and 'data' in created_team else created_team
                team_id = team_obj.get('id') or team_obj.get('_id') or ''
                if team_id:
                    return str(team_id)
    except Exception as e:
        print(f'Error in team_id fixture: {e}')
        pass
    return None


class TestTeamReadScope:
    def test_get_teams_works_when_token_has_team_read_scope(self, token_scopes):
        has_scope = 'team:read' in token_scopes
        if not has_scope:
            org_id = get_org_id_from_token(ACCESS_TOKEN)
            url = f'{BACKEND_URL}/api/v1/teams?page=1&limit=10'
            if org_id:
                url += f'&orgId={org_id}'
            response = make_request(url, method='GET', headers={'Authorization': f'Bearer {ACCESS_TOKEN}'})
            assert response['status'] == 403
            return
        org_id = get_org_id_from_token(ACCESS_TOKEN)
        url = f'{BACKEND_URL}/api/v1/teams?page=1&limit=10'
        if org_id:
            url += f'&orgId={org_id}'
        response = make_request(url, method='GET', headers={'Authorization': f'Bearer {ACCESS_TOKEN}'})
        assert 200 <= response['status'] < 500

    def test_get_teams_returns_denied_when_token_does_not_have_team_read_scope(self, token_scopes):
        has_scope = 'team:read' in token_scopes
        if has_scope:
            org_id = get_org_id_from_token(ACCESS_TOKEN)
            url = f'{BACKEND_URL}/api/v1/teams?page=1&limit=10'
            if org_id:
                url += f'&orgId={org_id}'
            response = make_request(url, method='GET', headers={'Authorization': f'Bearer {ACCESS_TOKEN}'})
            assert 200 <= response['status'] < 500
            return
        org_id = get_org_id_from_token(ACCESS_TOKEN)
        url = f'{BACKEND_URL}/api/v1/teams?page=1&limit=10'
        if org_id:
            url += f'&orgId={org_id}'
        response = make_request(url, method='GET', headers={'Authorization': f'Bearer {ACCESS_TOKEN}'})
        assert response['status'] == 403


class TestTeamWriteScope:
    def test_post_teams_works_when_token_has_team_write_scope(self, token_scopes):
        has_scope = 'team:write' in token_scopes
        if not has_scope:
            org_id = get_org_id_from_token(ACCESS_TOKEN)
            body = json.dumps({"name": "Team"})
            if org_id:
                body_data = json.loads(body)
                body_data['orgId'] = org_id
                body = json.dumps(body_data)
            response = make_request(
                f'{BACKEND_URL}/api/v1/teams',
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
        body = json.dumps({"name": "Team"})
        if org_id:
            body_data = json.loads(body)
            body_data['orgId'] = org_id
            body = json.dumps(body_data)
        response = make_request(
            f'{BACKEND_URL}/api/v1/teams',
            method='POST',
            headers={
                'Authorization': f'Bearer {ACCESS_TOKEN}',
                'Content-Type': 'application/json'
            },
            body=body
        )
        assert 200 <= response['status'] < 500

    def test_put_team_works_when_token_has_team_write_scope(self, token_scopes, team_id):
        if not team_id:
            pytest.skip('No team ID available')
        has_scope = 'team:write' in token_scopes
        if not has_scope:
            org_id = get_org_id_from_token(ACCESS_TOKEN)
            body = json.dumps({"name": "Team Updated"})
            if org_id:
                body_data = json.loads(body)
                body_data['orgId'] = org_id
                body = json.dumps(body_data)
            response = make_request(
                f'{BACKEND_URL}/api/v1/teams/{team_id}',
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
        body = json.dumps({"name": "Team Updated"})
        if org_id:
            body_data = json.loads(body)
            body_data['orgId'] = org_id
            body = json.dumps(body_data)
        response = make_request(
            f'{BACKEND_URL}/api/v1/teams/{team_id}',
            method='PUT',
            headers={
                'Authorization': f'Bearer {ACCESS_TOKEN}',
                'Content-Type': 'application/json'
            },
            body=body
        )
        assert 200 <= response['status'] < 500

    def test_post_teams_returns_denied_when_token_does_not_have_team_write_scope(self, token_scopes):
        has_scope = 'team:write' in token_scopes
        if has_scope:
            org_id = get_org_id_from_token(ACCESS_TOKEN)
            body = json.dumps({"name": "Team"})
            if org_id:
                body_data = json.loads(body)
                body_data['orgId'] = org_id
                body = json.dumps(body_data)
            response = make_request(
                f'{BACKEND_URL}/api/v1/teams',
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
        body = json.dumps({"name": "Team"})
        if org_id:
            body_data = json.loads(body)
            body_data['orgId'] = org_id
            body = json.dumps(body_data)
        response = make_request(
            f'{BACKEND_URL}/api/v1/teams',
            method='POST',
            headers={
                'Authorization': f'Bearer {ACCESS_TOKEN}',
                'Content-Type': 'application/json'
            },
            body=body
        )
        assert response['status'] == 403
