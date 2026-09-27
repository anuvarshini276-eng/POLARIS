from pydantic import BaseModel,Field
from fastapi import APIRouter,Depends
from sqlalchemy import select
from app.models.database import Resource,get_db
from app.core.security import admin
from app.services.settings import settings
from app.repositories.documents import audit
router=APIRouter(tags=['System configuration'])
class SettingsUpdate(BaseModel):
    allow_registration:bool=True
    allow_uploads:bool=True
    site_notice:str=Field(max_length=300)
@router.get('/settings')
def read_settings(db=Depends(get_db)):return settings(db)
@router.put('/settings')
def save_settings(body:SettingsUpdate,user=Depends(admin),db=Depends(get_db)):
    row=db.scalar(select(Resource).where(Resource.kind=='settings'))
    if not row:row=Resource(kind='settings',title='Platform settings');db.add(row)
    row.data=body.model_dump();audit(db,user,'settings.update','platform');db.commit();return row.data
