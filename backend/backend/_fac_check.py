from app.config import get_settings
get_settings.cache_clear()
from app.database import SessionLocal
from app.models import Result, Faculty, Student

db = SessionLocal()
total_results = db.query(Result).count()
results_with_faculty = db.query(Result).filter(Result.faculty_id.isnot(None)).count()
total_faculty = db.query(Faculty).count()
active_batch = db.execute(__import__('sqlalchemy').text(
    'SELECT id, filename, is_active FROM import_batches WHERE is_active=1 OR is_active=true LIMIT 1'
)).fetchone()
print('Total results:', total_results)
print('Results with faculty_id:', results_with_faculty)
print('Total faculty records:', total_faculty)
print('Active batch:', active_batch)
if total_faculty > 0:
    f = db.query(Faculty).first()
    print('First faculty:', f.faculty_name, f.id)
db.close()