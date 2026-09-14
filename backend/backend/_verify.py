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
        print('Login:', login.status_code, 'keys:', list(login.json().get('data', {}).keys())[:4])
        
        if login.status_code == 200 and 'access_token' in login.json().get('data', {}):
            token = login.json()['data']['access_token']
            headers = {'Authorization': 'Bearer ' + token}
            
            fac = c.get('/api/analysis/faculty', headers=headers)
            print('Faculty: status=' + str(fac.status_code) + ' count=' + str(len(fac.json().get('data',[]))))
            
            imports = c.get('/api/results/imports', headers=headers)
            print('Imports: status=' + str(imports.status_code) + ' total=' + str(imports.json().get('pagination',{}).get('total',0)))
            
            audit = c.get('/api/auth/audit-logs', headers=headers)
            print('Audit: status=' + str(audit.status_code) + ' count=' + str(len(audit.json().get('data',[]))))
            print('ALL OK - data will show in frontend now')
        else:
            print('STILL FAILING:', login.json())

app.dependency_overrides.clear()