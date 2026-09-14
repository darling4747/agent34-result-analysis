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
            
            fac = c.get('/api/analysis/faculty', headers=headers)
            fac_data = fac.json().get('data', [])
            print('Faculty count:', len(fac_data))
            if fac_data:
                f = fac_data[0]
                print('First entry name:', f.get('faculty_name'))
                print('Pass rate:', f.get('pass_rate'))
                print('Total students:', f.get('total_students'))
            else:
                print('Still empty — error:', fac.json().get('detail') or fac.status_code)
        else:
            print('Login still failed:', login.json())

app.dependency_overrides.clear()