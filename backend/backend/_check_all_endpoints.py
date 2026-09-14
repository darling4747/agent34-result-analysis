from app.config import get_settings
get_settings.cache_clear()
from app.database import SessionLocal, get_db
from app.main import app
from fastapi.testclient import TestClient
from unittest.mock import patch

def override_get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

app.dependency_overrides[get_db] = override_get_db

with patch('app.main.init_db'):
    with TestClient(app) as c:
        login = c.post('/api/auth/login', json={'email': 'admin@university.edu', 'password': 'Admin@Vignan2026!'})
        if login.status_code == 200 and 'access_token' in login.json().get('data', {}):
            token = login.json()['data']['access_token']
            headers = {'Authorization': 'Bearer ' + token}
            
            tests = [
                ('GET', '/health', None),
                ('GET', '/', None),
                ('GET', '/api/auth/me', None),
                ('GET', '/api/results/dataset-info', None),
                ('GET', '/api/results/imports', None),
                ('GET', '/api/auth/audit-logs', None),
                ('GET', '/api/analysis/summary', None),
                ('GET', '/api/analysis/grades', None),
                ('GET', '/api/analysis/courses', None),
                ('GET', '/api/analysis/sections', None),
                ('GET', '/api/analysis/faculty', None),
                ('GET', '/api/analysis/merit-list', None),
                ('GET', '/api/analysis/correlation', None),
                ('GET', '/api/analysis/historical', None),
                ('GET', '/api/analysis/interventions', None),
                ('GET', '/api/analysis/backlogs', None),
                ('GET', '/api/analysis/attainment-input', None),
                ('GET', '/api/auth/admin/users', None),
                ('GET', '/api/auth/mfa/status', None),
                ('GET', '/api/config', None),
            ]
            
            all_ok = True
            for method, url, body in tests:
                if method == 'GET':
                    r = c.get(url, headers=headers)
                else:
                    r = c.post(url, json=body, headers=headers)
                status = 'OK' if r.status_code == 200 else f'FAIL({r.status_code})'
                if r.status_code != 200:
                    all_ok = False
                print(f'  {method} {url}: {status}')
            
            print()
            print('ALL ENDPOINTS OK' if all_ok else 'SOME ENDPOINTS FAILED')
        else:
            print('Login failed:', login.json())

app.dependency_overrides.clear()