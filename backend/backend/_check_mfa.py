from app.config import get_settings
get_settings.cache_clear()
from app.database import SessionLocal
from app.models import User

db = SessionLocal()
admin = db.query(User).filter_by(email='admin@university.edu').first()
print('mfa_enabled:', admin.mfa_enabled)
print('mfa_secret_encrypted:', admin.mfa_secret_encrypted[:20] if admin.mfa_secret_encrypted else None)
print('mfa_recovery_codes:', admin.mfa_recovery_codes[:30] if admin.mfa_recovery_codes else None)
db.close()