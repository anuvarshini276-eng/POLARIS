import io
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import select
from docx import Document as WordDocument
from pypdf import PdfWriter
from app.main import app
from app.models.database import SessionLocal,User,Resource,Document,Chunk,Job
from app.core.security import hash_password
from app.services.processing import extract,validate_file,process_job

@pytest.fixture
def client():
    with TestClient(app) as value:yield value

def account(client,name,role='researcher'):
    with SessionLocal() as db:
        user=User(name=name,email=name+'@test.example',password=hash_password('Testing-123456'),role=role);db.add(user);db.commit()
    response=client.post('/api/v1/auth/login',json={'email':name+'@test.example','password':'Testing-123456'})
    return {'Authorization':'Bearer '+response.json()['access_token']}

@pytest.mark.parametrize('filename,mime,body',[('evil.exe','application/octet-stream',b'x'),('bad.txt','text/plain',b'\x00bad'),('bad.docx','application/vnd.openxmlformats-officedocument.wordprocessingml.document',b'not a zip'),('image.txt','image/png',b'hello')])
def test_rejects_invalid_uploads(filename,mime,body):
    from fastapi import HTTPException
    with pytest.raises(HTTPException):validate_file(filename,mime,body)

def test_docx_csv_pdf_extraction():
    doc=WordDocument();doc.add_paragraph('Methodology: Tracer sampling.');buf=io.BytesIO();doc.save(buf)
    assert 'Tracer sampling' in extract('research.docx',buf.getvalue())[0][1]
    assert extract('observations.csv',b'month,value\n1,42')[0][1].endswith('1,42')
    pdf=PdfWriter();pdf.add_blank_page(width=300,height=300);data=io.BytesIO();pdf.write(data)
    assert extract('scan.pdf',data.getvalue())==[(1,'')]

def test_cross_user_isolation_and_history_revocation(client):
    first=account(client,'sourceowner');second=account(client,'otherreader');admin=account(client,'securityadmin','admin')
    upload=client.post('/api/v1/documents',headers=first,data={'title':'Private krypton evidence','visibility':'private'},files={'file':('krypton.txt',b'Findings: Krypton fluorescence peaks at 430 units in this synthetic test.','text/plain')}).json();docid=upload['id']
    with SessionLocal() as db:jobid=db.scalar(select(Job.id).where(Job.document_id==docid))
    process_job(jobid)
    assert client.get('/api/v1/documents/'+docid,headers=second).status_code==404
    assert client.get('/api/v1/documents/'+docid+'/download',headers=second).status_code==404
    answer=client.post('/api/v1/chat',headers=first,json={'question':'krypton fluorescence','document_id':docid}).json();conv=answer['conversation_id']
    assert client.get('/api/v1/chat/conversations/'+conv,headers=second).status_code==404
    assert client.put('/api/v1/documents/'+docid,headers=second,json={'title':'Stolen'}).status_code==404
    assert client.get('/api/v1/search?q=krypton',headers=second).json()['total']==0
    assert client.post('/api/v1/chat',headers=second,json={'question':'krypton fluorescence'}).json()['sources']==[]

def test_media_draft_permissions(client):
    admin=account(client,'mediaadmin','admin')
    # Valid small PNG fixture; only public after explicit publication.
    import base64
    png=base64.b64decode('iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mP8/x8AAwMCAO+aGioAAAAASUVORK5CYII=')
    upload=client.post('/api/v1/media',headers=admin,data={'title':'Synthetic test image'},files={'file':('test.png',png,'image/png')})
    assert upload.status_code==201,upload.text
    item=upload.json()['id']
    assert client.get('/api/v1/media/'+item+'/file').status_code==404
    assert client.get('/api/v1/media').json()==[]
    assert client.post('/api/v1/media/'+item+'/publish',headers=admin).status_code==200
    assert client.get('/api/v1/media/'+item+'/file').status_code==200
    assert client.delete('/api/v1/media/'+item,headers=admin).status_code==200
    assert client.get('/api/v1/media/'+item+'/file').status_code==404

def test_pdf_page_citations(client):
    from pypdf.generic import DictionaryObject,NameObject,DecodedStreamObject
    writer=PdfWriter();page=writer.add_blank_page(width=300,height=300)
    font=DictionaryObject({NameObject('/Type'):NameObject('/Font'),NameObject('/Subtype'):NameObject('/Type1'),NameObject('/BaseFont'):NameObject('/Helvetica')})
    page[NameObject('/Resources')]=DictionaryObject({NameObject('/Font'):DictionaryObject({NameObject('/F1'):font})})
    stream=DecodedStreamObject();stream.set_data(b'BT /F1 12 Tf 20 250 Td (Findings: Synthetic neon tracer concentration was 7 units.) Tj ET')
    page[NameObject('/Contents')]=writer._add_object(stream)
    data=io.BytesIO();writer.write(data)
    headers=account(client,'pdfscientist')
    upload=client.post('/api/v1/documents',headers=headers,data={'title':'Neon tracer PDF'},files={'file':('neon.pdf',data.getvalue(),'application/pdf')}).json()
    with SessionLocal() as db:jobid=db.scalar(select(Job.id).where(Job.document_id==upload['id']))
    process_job(jobid)
    answer=client.post('/api/v1/chat',headers=headers,json={'question':'neon tracer concentration','document_id':upload['id']}).json()
    assert answer['sources'][0]['page']==1
    assert '7 units' in answer['answer']

def test_system_settings_authorization(client):
    admin=account(client,'settingsadmin','admin');researcher=account(client,'settingsresearcher')
    body={'allow_registration':False,'allow_uploads':True,'site_notice':'Configuration test'}
    assert client.put('/api/v1/settings',headers=researcher,json=body).status_code==403
    assert client.put('/api/v1/settings',headers=admin,json=body).status_code==200
    assert client.post('/api/v1/auth/register',json={'name':'Paused','email':'paused@example.org','password':'StrongPass-1234'}).status_code==403
    assert client.put('/api/v1/settings',headers=admin,json={**body,'allow_registration':True}).status_code==200
