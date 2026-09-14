import json
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
        print('Login response:', json.dumps(login.json(), indent=2)[:500])

app.dependency_overrides.clear()