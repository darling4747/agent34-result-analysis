import json, pathlib
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
        print('Login status:', login.status_code)
        if login.status_code == 200:
            token = login.json()['data']['access_token']
            headers = {'Authorization': 'Bearer ' + token}
            
            fac = c.get('/api/analysis/faculty', headers=headers)
            fac_data = fac.json().get('data', [])
            print('Faculty status:', fac.status_code, 'count:', len(fac_data))
            if fac_data:
                f = fac_data[0]
                print('Faculty sample keys:', list(f.keys()))
                print('Faculty name:', f.get('faculty_name'))
                print('Courses handled:', f.get('courses_handled'))
            
            imports = c.get('/api/results/imports', headers=headers)
            imp_data = imports.json()
            print('Imports status:', imports.status_code, 'total:', imp_data.get('pagination', {}).get('total', 0))
            if imp_data.get('data'):
                print('Import sample:', imp_data['data'][0].get('filename'))
            
            audit = c.get('/api/auth/audit-logs', headers=headers)
            aud_data = audit.json().get('data', [])
            print('Audit status:', audit.status_code, 'count:', len(aud_data))
            if aud_data:
                print('Audit sample action:', aud_data[0].get('action'))
        else:
            print('Login failed:', login.json())

app.dependency_overrides.clear()