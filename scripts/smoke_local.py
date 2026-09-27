"""Exercise the running local service without exposing generated demo credentials."""
import json
from pathlib import Path
import httpx
root=Path(__file__).resolve().parents[1]
with httpx.Client(base_url='http://127.0.0.1:8000',timeout=30) as client:
    for route in ['/','/repository','/map','/education','/analytics','/swagger','/redoc','/land.geojson','/api/v1/health','/api/v1/health/worker','/api/v1/stations','/api/v1/expeditions','/api/v1/datasets','/api/v1/media/library','/api/v1/settings']:
        response=client.get(route);assert response.status_code==200,(route,response.status_code)
    assert client.get('/api/v1/health/worker').json()['status']=='ok'
    accounts=json.loads((root/'data'/'demo-accounts.json').read_text())
    account=next(a for a in accounts if a['role']=='admin')
    response=client.post('/api/v1/auth/login',json={'email':account['email'],'password':account['password']});assert response.status_code==200
    session=response.json();client.headers['Authorization']='Bearer '+session['access_token']
    for route in ['/api/v1/users','/api/v1/audit-logs','/api/v1/notifications','/api/v1/chat/conversations','/api/v1/ai/generations','/api/v1/analytics/dashboard']:
        assert client.get(route).status_code==200,route
    result=client.post('/api/v1/chat',json={'question':'What were the zirconium tracer readings?'}).json()
    assert result['sources'] and all('zirconium' in s['title'].lower() for s in result['sources']),result
    assert '12, 18 and 24' in result['answer']
    result=client.post('/api/v1/chat',json={'question':'quantum unicorn teleportation'}).json()
    assert not result['sources'] and 'Sufficient evidence was not found' in result['answer']
    assert client.post('/api/v1/auth/logout',json={'refresh_token':session['refresh_token']}).status_code==200
    assert client.get('/api/v1/auth/me').status_code==401
print('Live smoke checks passed: routes, health, roles, media, settings, grounded retrieval, abstention and session revocation.')
