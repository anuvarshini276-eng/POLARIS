from pathlib import Path
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form, Query, Response
from sqlalchemy import select
from app.models.database import Document, Version, Chunk, Job, Event, get_db, uid
from app.core.security import current_user, require_user, moderator
from app.repositories.documents import visible_query, get_document, can_edit, serialize, audit, notify
from app.services.processing import validate_file
from app.services.storage import storage
from app.services.retrieval import retrieve
from app.schemas.requests import DocumentEdit, Moderate
from app.services.settings import settings
router=APIRouter(tags=['Research repository'])
@router.get('/documents')
def documents(q:str='',region:str='',domain:str='',category:str='',year:int|None=None,status:str='',mine:bool=False,page:int=Query(1,ge=1),limit:int=Query(12,ge=1,le=100),sort:str='newest',user=Depends(current_user),db=Depends(get_db)):
    query=visible_query(user)
    if q: query=query.where(Document.title.icontains(q)|Document.abstract.icontains(q))
    for field,value in [(Document.region,region),(Document.domain,domain),(Document.category,category),(Document.year,year),(Document.moderation,status)]:
        if value: query=query.where(field==value)
    if mine:
        if not user: raise HTTPException(401,'Sign in')
        query=query.where(Document.owner_id==user.id)
    query=query.order_by(Document.title if sort=='title' else Document.created_at.desc())
    items=list(db.scalars(query)); return {'items':[serialize(d) for d in items[(page-1)*limit:page*limit]],'total':len(items),'page':page,'pages':max(1,(len(items)+limit-1)//limit)}
@router.post('/documents',status_code=201)
async def upload(file:UploadFile=File(...),title:str=Form(...,min_length=2,max_length=300),region:str=Form('Antarctic'),domain:str=Form('Climate science'),category:str=Form('Research Papers'),year:int=Form(2025),visibility:str=Form('public'),user=Depends(require_user),db=Depends(get_db)):
    if user.role=='public': raise HTTPException(403,'Researcher access required')
    if not settings(db)['allow_uploads']: raise HTTPException(403,'Document uploads are currently paused')
    if region not in ('Arctic','Antarctic') or visibility not in ('public','private') or not 1800<=year<=2100: raise HTTPException(422,'Invalid metadata')
    data=await file.read(20*1024*1024+1); ext,mime=validate_file(file.filename,file.content_type,data)
    doc=Document(title=title,owner_id=user.id,region=region,domain=domain[:100],category=category[:100],year=year,visibility=visibility)
    db.add(doc); db.flush(); key=uid()+ext; storage().put(key,data)
    db.add(Version(document_id=doc.id,number=1,filename=Path(file.filename).name,storage_key=key,mime=mime,size=len(data)))
    db.add(Job(document_id=doc.id)); audit(db,user,'document.upload',doc.id); notify(db,user.id,f'Upload received: {title}'); db.add(Event(kind='upload',value=domain)); db.commit()
    return serialize(doc)
@router.get('/documents/{doc_id}')
def detail(doc_id:str,user=Depends(current_user),db=Depends(get_db)):
    doc=get_document(db,doc_id,user); doc.views+=1; db.commit()
    result=serialize(doc)
    historical=user and (user.id==doc.owner_id or user.role in ('admin','content_manager'))
    chunks=select(Chunk).where(Chunk.document_id==doc.id)
    if not historical: chunks=chunks.where(Chunk.version==doc.version)
    result['chunks']=[{'id':c.id,'page':c.page,'text':c.text,'position':c.position,'version':c.version} for c in db.scalars(chunks.order_by(Chunk.version.desc(),Chunk.position))]
    result['versions']=[{'number':v.number,'filename':v.filename,'size':v.size,'created_at':v.created_at} for v in db.scalars(select(Version).where(Version.document_id==doc.id).order_by(Version.number.desc()))]
    result['jobs']=[{'status':j.status,'error':j.error} for j in db.scalars(select(Job).where(Job.document_id==doc.id).order_by(Job.created_at.desc()).limit(3))]
    result['related']=[serialize(d) for d in db.scalars(visible_query(user).where(Document.domain==doc.domain,Document.id!=doc.id).limit(3))]
    return result
@router.put('/documents/{doc_id}')
def edit(doc_id:str,body:DocumentEdit,user=Depends(require_user),db=Depends(get_db)):
    doc=get_document(db,doc_id,user); can_edit(doc,user)
    for key,value in body.model_dump(exclude_none=True).items():
        if key=='tags': doc.meta={**doc.meta,'keywords':value}
        else: setattr(doc,key,value)
    if user.role not in ('admin','content_manager'): doc.moderation='UNDER_REVIEW'
    audit(db,user,'document.edit',doc.id); db.commit(); return serialize(doc)
@router.delete('/documents/{doc_id}')
def remove(doc_id:str,user=Depends(require_user),db=Depends(get_db)):
    doc=get_document(db,doc_id,user); can_edit(doc,user); doc.deleted=True; audit(db,user,'document.delete',doc.id); db.commit(); return {'ok':True}
@router.post('/documents/{doc_id}/versions')
async def version(doc_id:str,file:UploadFile=File(...),user=Depends(require_user),db=Depends(get_db)):
    doc=get_document(db,doc_id,user); can_edit(doc,user)
    if doc.processing in ('UPLOADED','PROCESSING'): raise HTTPException(409,'Wait for the current processing job')
    data=await file.read(20*1024*1024+1); ext,mime=validate_file(file.filename,file.content_type,data); key=uid()+ext; storage().put(key,data)
    doc.version+=1; doc.processing='UPLOADED'; doc.moderation='UNDER_REVIEW'
    db.add(Version(document_id=doc.id,number=doc.version,filename=Path(file.filename).name,storage_key=key,mime=mime,size=len(data))); db.add(Job(document_id=doc.id)); audit(db,user,'document.version',doc.id); db.commit(); return serialize(doc)
@router.post('/documents/{doc_id}/process')
def process(doc_id:str,user=Depends(require_user),db=Depends(get_db)):
    doc=get_document(db,doc_id,user); can_edit(doc,user)
    if db.scalar(select(Job).where(Job.document_id==doc.id,Job.status.in_(['QUEUED','PROCESSING']))): raise HTTPException(409,'Processing already queued')
    doc.processing='UPLOADED'; db.add(Job(document_id=doc.id)); db.commit(); return {'status':'QUEUED'}
@router.post('/documents/{doc_id}/moderation')
def moderate(doc_id:str,body:Moderate,user=Depends(moderator),db=Depends(get_db)):
    doc=get_document(db,doc_id,user)
    allowed={'UPLOADED':['UNDER_REVIEW','REJECTED'],'UNDER_REVIEW':['APPROVED','REJECTED'],'APPROVED':['PUBLISHED','REJECTED'],'REJECTED':['UNDER_REVIEW'],'PUBLISHED':['UNDER_REVIEW','REJECTED']}
    if body.status not in allowed[doc.moderation]: raise HTTPException(409,'Invalid moderation transition')
    if body.status in ('APPROVED','PUBLISHED') and doc.processing!='COMPLETED': raise HTTPException(409,'Processing must finish first')
    doc.moderation=body.status; doc.meta={**doc.meta,'review_note':body.reason}; notify(db,doc.owner_id,f'{doc.title}: {body.status}. {body.reason}'); audit(db,user,'document.'+body.status.lower(),doc.id); db.commit(); return serialize(doc)
@router.get('/documents/{doc_id}/download')
def download(doc_id:str,version:int|None=None,user=Depends(current_user),db=Depends(get_db)):
    doc=get_document(db,doc_id,user)
    if version and version!=doc.version and (not user or (user.id!=doc.owner_id and user.role not in ('admin','content_manager'))): raise HTTPException(403,'Historical versions are restricted')
    v=db.scalar(select(Version).where(Version.document_id==doc.id,Version.number== (version or doc.version)))
    if not v: raise HTTPException(404,'Version not found')
    doc.downloads+=1; db.add(Event(kind='download',value=doc.id)); db.commit()
    return Response(storage().get(v.storage_key),media_type=v.mime,headers={'Content-Disposition':f'attachment; filename="polaris-{doc.id}{Path(v.filename).suffix}"'})
@router.get('/search')
def search(q:str=Query(...,min_length=2,max_length=1000),region:str='',domain:str='',year:int|None=None,station:str='',author:str='',organization:str='',category:str='',user=Depends(current_user),db=Depends(get_db)):
    hits=retrieve(db,q,user,top_k=100); output=[]; seen=set()
    for hit in hits:
        if hit['document_id'] in seen: continue
        doc=get_document(db,hit['document_id'],user)
        if any([region and doc.region!=region,domain and doc.domain!=domain,year and doc.year!=year,category and doc.category!=category,station and station.lower() not in str(doc.meta.get('station','')).lower(),author and author.lower() not in str(doc.meta.get('authors','')).lower(),organization and organization.lower() not in str(doc.meta.get('organization','')).lower()]): continue
        seen.add(doc.id); output.append({**serialize(doc),'relevance':hit['relevance'],'excerpt':hit['excerpt']})
    db.add(Event(kind='search',value=q)); db.commit(); return {'items':output,'total':len(output)}
@router.get('/search/suggestions')
def suggestions(q:str='',user=Depends(current_user),db=Depends(get_db)):
    return [d.title for d in db.scalars(visible_query(user).where(Document.title.icontains(q)).limit(6))]
