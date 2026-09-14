"""Development seed: create roles, permissions, and 7 demo user accounts."""
from __future__ import annotations
import os, sys, pathlib
sys.path.insert(0, str(pathlib.Path(__file__).parent))
# Uses DATABASE_URL from .env (PostgreSQL)

from app.config import get_settings
get_settings.cache_clear()
from app.database import engine, SessionLocal, init_db
from app.models import Base, Role, User
from app import models  # noqa
from app.services.auth_service import AuthService
from app.security.password import generate_temp_password, hash_password
from datetime import datetime, timezone, timedelta

SEED_USERS = [
    {'email': 'admin@university.edu',       'full_name': 'Platform Administrator', 'role': 'PLATFORM_ADMIN', 'dept': None},
    {'email': 'dean@university.edu',        'full_name': 'Dr. V. Dean',            'role': 'DEAN',           'dept': None},
    {'email': 'hod.cse@university.edu',     'full_name': 'Dr. HOD CSE',            'role': 'HOD',            'dept': 'CSE'},
    {'email': 'faculty@university.edu',     'full_name': 'Dr. R. Faculty',         'role': 'FACULTY',        'dept': 'CSE'},
    {'email': 'iqac@university.edu',        'full_name': 'IQAC Coordinator',       'role': 'IQAC',           'dept': None},
    {'email': 'management@university.edu',  'full_name': 'Management User',        'role': 'MANAGEMENT',     'dept': None},
    {'email': 'auditor@university.edu',     'full_name': 'System Auditor',         'role': 'AUDITOR',        'dept': None},
]

def main():
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        svc = AuthService(db, get_settings())
        svc.seed_roles_and_permissions()
        print('Roles and permissions seeded.')
        credentials = []
        for u in SEED_USERS:
            existing = db.query(User).filter_by(email=u['email'].lower()).first()
            if existing:
                print(f'  SKIP (exists): {u["email"]}')
                continue
            role = db.query(Role).filter_by(name=u['role']).first()
            if not role:
                print(f'  ERROR: role {u["role"]} not found')
                continue
            temp_pw = generate_temp_password()
            user = User(
                email=u['email'].lower(), full_name=u['full_name'],
                role_id=role.id, department=u.get('dept'),
                is_active=True, password_hash=hash_password(temp_pw),
                must_change_password=True,
                temp_password_expires_at=datetime.now(timezone.utc) + timedelta(hours=720),
            )
            db.add(user)
            db.commit()
            credentials.append({'email': u['email'], 'role': u['role'], 'pw': temp_pw})
            print(f'  CREATED: {u["email"]} [{u["role"]}]')
        print()
        if credentials:
            print('=== TEMPORARY CREDENTIALS - SHOWN ONCE ===')
            for c in credentials:
                print(f'  {c["email"]:42s}  [{c["role"]:16s}]  pw: {c["pw"]}')
            print()
            print('All users must change password on first login.')
        else:
            print('All users already exist - no new credentials generated.')
    finally:
        db.close()

if __name__ == '__main__':
    main()