from app.config import get_settings
get_settings.cache_clear()
from app.database import SessionLocal
from app.models import ImportBatch, Result
from sqlalchemy import func

db = SessionLocal()
# Find the active batch and check what columns were in the uploaded file
active = db.query(ImportBatch).filter(ImportBatch.is_active == True).first()
print('Active batch:', active.id, active.filename, active.academic_year, 'Sem', active.semester)

# Check a sample of results from this batch to see what data we have
sample = db.query(Result).filter(Result.import_batch_id == active.id).limit(3).all()
for r in sample:
    print(f'  Result: student_id={r.student_id} course_id={r.course_id} faculty_id={r.faculty_id} section={r.section} dept? via student')

# How many results have faculty_id set for this batch?
with_fac = db.query(func.count(Result.id)).filter(
    Result.import_batch_id == active.id,
    Result.faculty_id.isnot(None)
).scalar()
total = db.query(func.count(Result.id)).filter(Result.import_batch_id == active.id).scalar()
print(f'Batch {active.id}: {with_fac}/{total} results have faculty_id')
db.close()