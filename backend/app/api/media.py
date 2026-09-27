from pathlib import Path
from fastapi import APIRouter,Depends,UploadFile,File,Form,HTTPException,Response
from sqlalchemy import select
from app.models.database import Resource,get_db,uid
from app.core.security import moderator,current_user
from app.services.storage import storage
from app.repositories.documents import audit
router=APIRouter(tags=['Media management'])
def accessible(item,user):
    return item and item.kind=='media' and (item.data.get('status')=='PUBLISHED' or (user and user.role in ('admin','content_manager')))
@router.get('/media/library')
def library(user=Depends(current_user),db=Depends(get_db)):
    return [{'id':m.id,'title':m.title,**{k:v for k,v in m.data.items() if k!='storage_key'}} for m in db.scalars(select(Resource).where(Resource.kind=='media')) if accessible(m,user)]
@router.post('/media',status_code=201)
async def upload_media(file:UploadFile=File(...),title:str=Form(...,min_length=2,max_length=200),description:str=Form('',max_length=2000),region:str=Form('Antarctic'),user=Depends(moderator),db=Depends(get_db)):
    data=await file.read(20*1024*1024+1)
    if not data or len(data)>20*1024*1024: raise HTTPException(400,'Media must be under 20 MB')
    ext=Path(file.filename).suffix.lower()
    types={'.png':('image/png',data.startswith(b'\x89PNG\r\n\x1a\n')),'.jpg':('image/jpeg',data.startswith(b'\xff\xd8\xff')),'.jpeg':('image/jpeg',data.startswith(b'\xff\xd8\xff')),'.webp':('image/webp',data[:4]==b'RIFF' and data[8:12]==b'WEBP'),'.mp4':('video/mp4',data[4:8]==b'ftyp')}
    if ext not in types or not types[ext][1] or file.content_type not in (types[ext][0],'application/octet-stream'): raise HTTPException(400,'Upload a valid PNG, JPEG, WebP or MP4 file')
    key=uid()+ext; storage().put(key,data)
    item=Resource(kind='media',title=title,data={'description':description,'region':region,'mime':types[ext][0],'storage_key':key,'status':'DRAFT','owner_id':user.id,'demo':False});db.add(item);db.flush();audit(db,user,'media.upload',item.id);db.commit()
    return {'id':item.id,'title':item.title,'status':'DRAFT'}
@router.post('/media/{item_id}/publish')
def publish(item_id:str,user=Depends(moderator),db=Depends(get_db)):
    item=db.get(Resource,item_id)
    if not item or item.kind!='media': raise HTTPException(404,'Media not found')
    item.data={**item.data,'status':'PUBLISHED'};audit(db,user,'media.publish',item.id);db.commit();return {'ok':True}
@router.delete('/media/{item_id}')
def delete(item_id:str,user=Depends(moderator),db=Depends(get_db)):
    item=db.get(Resource,item_id)
    if not item or item.kind!='media': raise HTTPException(404,'Media not found')
    item.data={**item.data,'status':'ARCHIVED'};audit(db,user,'media.archive',item.id);db.commit();return {'ok':True}
@router.get('/media/{item_id}/file')
def file(item_id:str,user=Depends(current_user),db=Depends(get_db)):
    item=db.get(Resource,item_id)
    if not accessible(item,user): raise HTTPException(404,'Media not found')
    return Response(storage().get(item.data['storage_key']),media_type=item.data['mime'],headers={'Cache-Control':'private, no-store'})
