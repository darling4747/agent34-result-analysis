import pathlib, json
from fastapi.testclient import TestClient
from unittest.mock import patch
from app.config import get_settings
get_settings.cache_clear()
from app.main import app

with patch('app.main.init_db'):
    with TestClient(app) as c:
        from app.database import SessionLocal
        from app.models import User
        db = SessionLocal()
        admin = db.query(User).filter_by(email='admin@university.edu').first()
        db.close()
        
        if not admin:
            pathlib.Path('_diag.json').write_text(json.dumps({'error': 'no admin user'}))
        else:
            login = c.post('/api/auth/login', json={'email': 'admin@university.edu', 'password': 'Admin@Vignan2026!'})
            if login.status_code != 200:
                pathlib.Path('_diag.json').write_text(json.dumps({'login_fail': login.status_code, 'body': str(login.json())}))
            else:
                token = login.json()['data']['access_token']
                headers = {'Authorization': f'Bearer {token}'}
                fac = c.get('/api/analysis/faculty', headers=headers)
                imports = c.get('/api/results/imports', headers=headers)
                audit = c.get('/api/auth/audit-logs', headers=headers)
                pathlib.Path('_diag.json').write_text(json.dumps({
                    'faculty': {'status': fac.status_code, 'count': len(fac.json().get('data',[])), 'sample': fac.json().get('data',[])[:1]},
                    'imports': {'status': imports.status_code, 'count': len(imports.json().get('data',[])), 'total': imports.json().get('pagination',{}).get('total',0)},
                    'audit': {'status': audit.status_code, 'count': len(audit.json().get('data',[]))},
                }, indent=2))