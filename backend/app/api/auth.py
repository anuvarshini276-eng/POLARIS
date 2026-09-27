import time
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select, update
from app.models.database import User, RefreshSession, get_db
from app.schemas.requests import Login, Register, Refresh
from app.core.security import hash_password, verify_password, tokens, token_hash, require_user
from app.repositories.documents import audit
from app.services.settings import settings
router=APIRouter(prefix='/auth',tags=['Authentication'])
@router.post('/register',status_code=201)
def register(body:Register,db=Depends(get_db)):
    if not settings(db)['allow_registration']:raise HTTPException(403,'New account registration is currently paused')
    if db.scalar(select(User).where(User.email==body.email)): raise HTTPException(409,'Email already registered')
    user=User(name=body.name,email=body.email,password=hash_password(body.password),role='researcher'); db.add(user); db.flush()
    audit(db,user,'account.register',user.id); return tokens(db,user)
@router.post('/login')
def login(body:Login,db=Depends(get_db)):
    user=db.scalar(select(User).where(User.email==body.email.lower().strip()))
    if user and user.locked_until>time.time(): raise HTTPException(429,'Account temporarily locked. Try again in 15 minutes.')
    if not user or not user.active or not verify_password(body.password,user.password):
        if user:
            user.failures+=1
            if user.failures>=5: user.locked_until=time.time()+900
            db.commit()
        raise HTTPException(401,'Invalid email or password')
    user.failures=0; user.locked_until=0; audit(db,user,'auth.login',user.id)
    return tokens(db,user)
@router.post('/refresh')
def refresh(body:Refresh,db=Depends(get_db)):
    session=db.scalar(select(RefreshSession).where(RefreshSession.token_hash==token_hash(body.refresh_token)))
    if not session or session.revoked or session.expires<time.time(): raise HTTPException(401,'Invalid refresh session')
    user=db.get(User,session.user_id)
    if not user.active: raise HTTPException(401,'Account disabled')
    changed=db.execute(update(RefreshSession).where(RefreshSession.id==session.id,RefreshSession.revoked==False).values(revoked=True))
    if not changed.rowcount: raise HTTPException(401,'Refresh token already rotated')
    return tokens(db,user)
@router.post('/logout')
def logout(body:Refresh,user=Depends(require_user),db=Depends(get_db)):
    session=db.scalar(select(RefreshSession).where(RefreshSession.token_hash==token_hash(body.refresh_token),RefreshSession.user_id==user.id))
    if session: session.revoked=True
    audit(db,user,'auth.logout',user.id); db.commit(); return {'ok':True}
@router.get('/me')
def me(user=Depends(require_user)): return {'id':user.id,'name':user.name,'email':user.email,'role':user.role}
