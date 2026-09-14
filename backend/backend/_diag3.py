import json, pathlib
from app.config import get_settings
get_settings.cache_clear()

# Use the real DB directly without test overrides
from app.database import SessionLocal
from app.main import app
from fastapi.testclient import TestClient
from app.database import get_db

# Override get_db to use production DB (not test override)
def override_get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

app.dependency_overrides[get_db] = override_get_db

from unittest.mock import patch
with patch('app.main.init_db'):
    with TestClient(app) as c:
        login = c.post('/api/auth/login', json={'email': 'admin@university.edu', 'password': 'Admin@Vignan2026!'})
        print(f'Login status: {login.status_code}')
        if login.status_code == 200:
            token = login.json()['data']['access_token']
            headers = {'Authorization': f'Bearer {token}'}
            
            # Check faculty
            fac = c.get('/api/analysis/faculty', headers=headers)
            print(f'Faculty: status={fac.status_code} count={len(fac.json().get(\"data\",[]))}')
            if fac.json().get('data'):
                print(f'Faculty sample: {fac.json()[\"data\"][0]}')
            
            # Check imports
            imports = c.get('/api/results/imports', headers=headers)
            print(f'Imports: status={imports.status_code} count={imports.json().get(\"pagination\",{}).get(\"total\",0)}')
            
            # Check audit logs
            audit = c.get('/api/auth/audit-logs', headers=headers)
            print(f'Audit: status={audit.status_code} count={len(audit.json().get(\"data\",[]))}')
        else:
            print(f'Login failed: {login.json()}')

app.dependency_overrides.clear()