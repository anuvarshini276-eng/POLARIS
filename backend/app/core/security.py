import hashlib, hmac, secrets, time
import jwt
from fastapi import Depends, HTTPException
from fastapi.security import HTTPBearer
from sqlalchemy import select
from app.models.database import User, RefreshSession, get_db
from app.core.config import SECRET

bearer=HTTPBearer(auto_error=False)
def hash_password(password):
    salt=secrets.token_hex(16)
    return salt+':'+hashlib.scrypt(password.encode(),salt=salt.encode(),n=16384,r=8,p=1).hex()
def verify_password(password, encoded):
    salt, expected=encoded.split(':')
    return hmac.compare_digest(hashlib.scrypt(password.encode(),salt=salt.encode(),n=16384,r=8,p=1).hex(), expected)
def token_hash(token): return hashlib.sha256(token.encode()).hexdigest()
def tokens(db,user):
    refresh=secrets.token_urlsafe(48)
    session=RefreshSession(user_id=user.id,token_hash=token_hash(refresh),expires=time.time()+7*86400)
    db.add(session); db.flush()
    access=jwt.encode({'sub':user.id,'sid':session.id,'exp':int(time.time())+900,'iat':int(time.time())},SECRET,algorithm='HS256')
    db.commit()
    return {'access_token':access,'refresh_token':refresh,'token_type':'bearer','user':{'id':user.id,'name':user.name,'email':user.email,'role':user.role}}
def current_user(credentials=Depends(bearer),db=Depends(get_db)):
    if not credentials: return None
    try:
        payload=jwt.decode(credentials.credentials,SECRET,algorithms=['HS256'])
        user=db.get(User,payload['sub']); session=db.get(RefreshSession,payload['sid'])
        if not user or not user.active or not session or session.revoked or session.expires<time.time(): raise ValueError()
        return user
    except (jwt.PyJWTError,ValueError,KeyError): raise HTTPException(401,'Session expired. Please sign in again.')
def require_user(user=Depends(current_user)):
    if not user: raise HTTPException(401,'Sign in to continue')
    return user
def moderator(user=Depends(require_user)):
    if user.role not in ('admin','content_manager'): raise HTTPException(403,'Content manager access required')
    return user
def researcher(user=Depends(require_user)):
    if user.role=='public': raise HTTPException(403,'Researcher access required')
    return user
def admin(user=Depends(require_user)):
    if user.role!='admin': raise HTTPException(403,'Administrator access required')
    return user
