import json, pathlib
from app.config import get_settings
get_settings.cache_clear()
from app.security.password import hash_password, verify_password
from app.database import SessionLocal
from app.models import User, Role

db = SessionLocal()
admin = db.query(User).filter_by(email='admin@university.edu').first()
if admin:
    print(f'Found admin: id={admin.id} active={admin.is_active} must_change={admin.must_change_password}')
    print(f'hash starts with: {admin.password_hash[:10]}')
    ok = verify_password('Admin@Vignan2026!', admin.password_hash)
    print(f'verify Admin@Vignan2026!: {ok}')
    # Try test_auth fixture password
    ok2 = verify_password('TestPass99!X', admin.password_hash)
    print(f'verify TestPass99!X: {ok2}')
    ok3 = verify_password('FixturePass99!X', admin.password_hash)
    print(f'verify FixturePass99!X: {ok3}')
    role = db.query(Role).filter_by(id=admin.role_id).first()
    print(f'Role: {role.name if role else None}')
else:
    print('admin NOT found')
db.close()