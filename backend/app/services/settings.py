from sqlalchemy import select
from app.models.database import Resource
DEFAULTS={'allow_registration':True,'allow_uploads':True,'site_notice':'Synthetic demonstration · not official government data'}
def settings(db):
    row=db.scalar(select(Resource).where(Resource.kind=='settings'))
    return {**DEFAULTS,**(row.data if row else {})}
