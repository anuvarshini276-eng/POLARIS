import os, sys, tempfile
from pathlib import Path
os.environ['DATA_DIR']=tempfile.mkdtemp(prefix='polaris-test-')
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'backend'))
from fastapi.testclient import TestClient
from app.main import app
from app.models.database import *
from app.core.security import hash_password
from app.services.processing import process_job, chunk_text
from app.services.retrieval import retrieve
from sqlalchemy import select

def test_complete_research_workflow():
    with TestClient(app) as client:
        register=client.post('/api/v1/auth/register',json={'name':'Researcher','email':'research@example.org','password':'StrongPass-1234'})
        assert register.status_code==201
        credentials=register.json(); headers={'Authorization':'Bearer '+credentials['access_token']}
        with SessionLocal() as db:
            admin=User(name='Admin',email='admin@example.org',password=hash_password('AdminPass-1234'),role='admin'); db.add(admin); db.commit()
        adm=client.post('/api/v1/auth/login',json={'email':'admin@example.org','password':'AdminPass-1234'}).json(); ah={'Authorization':'Bearer '+adm['access_token']}
        bad=client.post('/api/v1/documents',headers=headers,data={'title':'Bad file'},files={'file':('bad.pdf',b'not pdf','application/pdf')}); assert bad.status_code==400
        upload=client.post('/api/v1/documents',headers=headers,data={'title':'Krill carbon field study','visibility':'private'},files={'file':('study.txt',b'Abstract: Krill carbon transport observations.\nMethodology: Sampling water.\nFindings: Synthetic krill transport varies seasonally.\nLimitations: Synthetic data.','text/plain')})
        assert upload.status_code==201,upload.text
        doc=upload.json(); docid=doc['id']
        assert client.get('/api/v1/documents/'+docid).status_code==404
        assert client.post('/api/v1/documents/'+docid+'/moderation',headers=headers,json={'status':'APPROVED'}).status_code==403
        with SessionLocal() as db: job=db.scalar(select(Job).where(Job.document_id==docid)); jobid=job.id
        process_job(jobid)
        detail=client.get('/api/v1/documents/'+docid,headers=headers).json(); assert detail['processing']=='COMPLETED'; assert detail['moderation']=='UPLOADED'; assert detail['chunks']
        answer=client.post('/api/v1/chat',headers=headers,json={'question':'What does krill carbon transport show?','document_id':docid}).json(); assert answer['sources'][0]['document_id']==docid
        assert client.get('/api/v1/search?q=krill').json()['total']==0
        assert client.post('/api/v1/chat',headers=headers,json={'question':'unicorn spaceship teleportation'}).json()['sources']==[]
        for state in ['UNDER_REVIEW','APPROVED','PUBLISHED']:
            assert client.post('/api/v1/documents/'+docid+'/moderation',headers=ah,json={'status':state}).status_code==200
        assert client.get('/api/v1/documents/'+docid).status_code==404
        assert client.put('/api/v1/documents/'+docid,headers=ah,json={'visibility':'public'}).status_code==200
        assert client.get('/api/v1/search?q=krill').json()['total']==1
        assert client.get('/api/v1/documents/'+docid+'/download').status_code==200
        assert client.post('/api/v1/ai/generate-content',headers=headers,json={'document_id':docid}).status_code==200
        quiz=client.post('/api/v1/ai/generate-quiz',headers=ah,json={'question':'Create quiz','document_id':docid}).json()
        result=client.post('/api/v1/quizzes/'+quiz['id']+'/attempts',json={'answers':[1]}); assert result.json()['score']==1
        assert client.get('/api/v1/users',headers=headers).status_code==403
        assert client.get('/api/v1/audit-logs',headers=ah).status_code==200
        assert client.post('/api/v1/auth/logout',headers=headers,json={'refresh_token':credentials['refresh_token']}).status_code==200
        assert client.get('/api/v1/auth/me',headers=headers).status_code==401
        assert client.post('/api/v1/auth/refresh',json={'refresh_token':credentials['refresh_token']}).status_code==401

def test_chunk_overlap():
    chunks=chunk_text(' '.join(str(i) for i in range(400)))
    assert chunks[0].split()[-35:]==chunks[1].split()[:35]
    assert chunks[-1].split()[-1]=='399'
