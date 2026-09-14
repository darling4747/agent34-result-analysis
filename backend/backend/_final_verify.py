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
        print('=== Login ===', 'OK' if login.status_code == 200 and 'access_token' in login.json().get('data',{}) else 'FAIL')
        
        if login.status_code == 200 and 'access_token' in login.json().get('data', {}):
            token = login.json()['data']['access_token']
            headers = {'Authorization': 'Bearer ' + token}
            
            print()
            print('=== FACULTY ANALYSIS ===')
            fac = c.get('/api/analysis/faculty', headers=headers)
            fac_data = fac.json().get('data', [])
            print('Status:', fac.status_code)
            print('Records:', len(fac_data))
            for f in fac_data[:3]:
                print(' -', f.get('faculty_name'), '| Pass:', f.get('pass_rate'), '| Students:', f.get('total_students'))
            
            print()
            print('=== IMPORT HISTORY (Results page) ===')
            imports = c.get('/api/results/imports', headers=headers)
            imp = imports.json()
            print('Status:', imports.status_code)
            print('Total imports:', imp.get('pagination',{}).get('total',0))
            for item in imp.get('data', [])[:3]:
                print(' -', item.get('filename'), '| Status:', item.get('status'), '| Active:', item.get('is_active'))
            
            print()
            print('=== AUDIT LOGS ===')
            audit = c.get('/api/auth/audit-logs', headers=headers)
            aud = audit.json()
            print('Status:', audit.status_code)
            print('Entries:', len(aud.get('data', [])))
            for a in aud.get('data', [])[:3]:
                print(' -', a.get('action'), '| Success:', a.get('success'), '| Time:', a.get('created_at','')[:19])

app.dependency_overrides.clear()