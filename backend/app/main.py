import logging, time, uuid
from collections import defaultdict, deque
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from app.models.database import Base, engine
from app.core.config import ROOT
from app.api import auth, documents, research, media, settings
from app.services.rate_limit import allowed

logging.basicConfig(level=logging.INFO,format='%(message)s')
@asynccontextmanager
async def lifespan(app):
    Base.metadata.create_all(engine)
    yield
app=FastAPI(title='POLARIS Research API',description='Polar Research Intelligence, Knowledge & Outreach System. Synthetic local demonstration.',version='1.0.0',docs_url='/swagger',redoc_url='/redoc',lifespan=lifespan)
limits=defaultdict(deque)
@app.middleware('http')
async def security(request:Request,call_next):
    request_id=str(uuid.uuid4()); start=time.time(); key=(request.client.host,request.url.path.startswith('/api/v1/auth'))
    if request.url.path.startswith('/api'):
        if int(request.headers.get('content-length','0'))>22*1024*1024: return JSONResponse({'detail':'Request exceeds the upload size limit'},status_code=413)
        if not allowed(*key): return JSONResponse({'detail':'Too many requests. Try again shortly.'},status_code=429)
    response=await call_next(request)
    if request.url.path.startswith('/api'): response.headers['Cache-Control']='no-store'
    response.headers.update({'X-Request-ID':request_id,'X-Content-Type-Options':'nosniff','X-Frame-Options':'DENY','Referrer-Policy':'same-origin','Content-Security-Policy':"default-src 'self'; script-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net; style-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net; img-src 'self' data: blob: https://*.tile.openstreetmap.org https://fastapi.tiangolo.com; connect-src 'self'; font-src 'self' data:; media-src 'self' blob:; frame-ancestors 'none'"})
    logging.info('{"request_id":"%s","method":"%s","path":"%s","status":%s,"ms":%s}',request_id,request.method,request.url.path,response.status_code,int((time.time()-start)*1000))
    return response
for router in (auth.router,documents.router,research.router,media.router,settings.router): app.include_router(router,prefix='/api/v1')
dist=ROOT/'frontend'/'dist'
if dist.exists():
    app.mount('/assets',StaticFiles(directory=dist/'assets'),name='assets')
    @app.get('/{path:path}',include_in_schema=False)
    def spa(path:str):
        if path.startswith('api/'): return JSONResponse({'detail':'Not found'},status_code=404)
        candidate=(dist/path).resolve()
        if candidate.is_relative_to(dist.resolve()) and candidate.is_file(): return FileResponse(candidate)
        return FileResponse(dist/'index.html')
