import time, logging
from sqlalchemy import select
from app.models.database import SessionLocal, Job, Base, engine, now
from app.services.processing import process_job
from app.core.config import DATA

def run():
    Base.metadata.create_all(engine)
    # A dedicated single local worker recovers its durable in-flight jobs on restart.
    with SessionLocal() as db:
        for job in db.scalars(select(Job).where(Job.status=='PROCESSING')):
            job.status='QUEUED'; job.updated_at=now()
        db.commit()
    while True:
        (DATA/'worker-heartbeat').write_text(str(time.time()))
        with SessionLocal() as db: jobs=list(db.scalars(select(Job.id).where(Job.status=='QUEUED').limit(10)))
        for job in jobs: process_job(job)
        time.sleep(1)
if __name__=='__main__': run()
