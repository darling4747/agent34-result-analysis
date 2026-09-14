from app.config import get_settings
get_settings.cache_clear()
from app.database import SessionLocal
from app.models import User, MFARecoveryCode

db = SessionLocal()
# Disable MFA on ALL users so everyone can log in normally
users = db.query(User).all()
for u in users:
    u.mfa_enabled = False
    u.mfa_secret_encrypted = None
    u.must_change_password = False
    u.temp_password_expires_at = None
    u.is_active = True
    # Delete recovery codes
    db.query(MFARecoveryCode).filter_by(user_id=u.id).delete()
    print(f'MFA disabled for {u.email}')

db.commit()
db.close()
print('Done. All users can now log in without MFA.')