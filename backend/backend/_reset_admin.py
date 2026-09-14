import json, pathlib
from app.config import get_settings
get_settings.cache_clear()
from app.database import SessionLocal
from app.models import User
from app.security.password import hash_password, verify_password

db = SessionLocal()
admin = db.query(User).filter_by(email='admin@university.edu').first()
if admin:
    new_pw = 'Admin@Vignan2026!'
    admin.password_hash = hash_password(new_pw)
    admin.must_change_password = False
    admin.temp_password_expires_at = None
    admin.is_active = True
    db.commit()
    db.refresh(admin)
    ok = verify_password(new_pw, admin.password_hash)
    print(f'Admin reset OK. verify={ok} must_change={admin.must_change_password} active={admin.is_active}')
else:
    print('admin not found')
db.close()