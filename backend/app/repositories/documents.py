from sqlalchemy import select, or_, and_
from fastapi import HTTPException
from app.models.database import Document, Audit, Notification

def visible_query(user=None):
    query=select(Document).where(Document.deleted==False)
    if user and user.role in ('admin','content_manager'): return query
    public=and_(Document.moderation=='PUBLISHED',Document.visibility=='public')
    return query.where(or_(public,Document.owner_id==user.id) if user else public)
def get_document(db,doc_id,user=None):
    doc=db.scalar(visible_query(user).where(Document.id==doc_id))
    if not doc: raise HTTPException(404,'Document not found')
    return doc
def can_edit(doc,user):
    if doc.owner_id!=user.id and user.role not in ('admin','content_manager'): raise HTTPException(403,'You cannot edit this submission')
def audit(db,user,action,target): db.add(Audit(user_id=user.id if user else None,action=action,target=str(target)))
def notify(db,user_id,text): db.add(Notification(user_id=user_id,text=text))
def serialize(doc):
    return {c.name:getattr(doc,c.name) for c in doc.__table__.columns if c.name!='deleted'}
