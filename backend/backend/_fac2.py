from app.config import get_settings
get_settings.cache_clear()
from app.database import SessionLocal
from app.models import Result, Faculty, ImportBatch
from sqlalchemy import func

db = SessionLocal()
total_results = db.query(Result).count()
results_with_faculty = db.query(Result).filter(Result.faculty_id.isnot(None)).count()
total_faculty = db.query(Faculty).count()
active = db.query(ImportBatch).filter(ImportBatch.is_active == True).first()
print('Total results:', total_results)
print('Results WITH faculty_id set:', results_with_faculty)
print('Total Faculty rows:', total_faculty)
print('Active batch:', active.id if active else None, active.filename if active else 'NONE')
if total_results > 0:
    sample = db.query(Result).first()
    print('Sample result faculty_id:', sample.faculty_id)
db.close()