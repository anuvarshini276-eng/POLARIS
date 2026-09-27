import io, re, zipfile
from pathlib import Path
from sqlalchemy import select, delete, update
from pypdf import PdfReader
from docx import Document as Docx
from fastapi import HTTPException
from app.core.config import MAX_FILE
from app.models.database import Document, Version, Chunk, Job, SessionLocal, now
from app.services.storage import storage
from app.ai.providers import embeddings, words
from app.repositories.documents import notify

MIMES={'.pdf':'application/pdf','.docx':'application/vnd.openxmlformats-officedocument.wordprocessingml.document','.txt':'text/plain','.csv':'text/csv'}
def validate_file(filename,mime,data):
    ext=Path(filename).suffix.lower()
    if ext not in MIMES: raise HTTPException(400,'Upload PDF, DOCX, TXT or CSV')
    if not data or len(data)>MAX_FILE: raise HTTPException(400,'File must contain data and be at most 20 MB')
    accepted={MIMES[ext],'application/octet-stream'}
    if ext=='.csv': accepted|={'application/vnd.ms-excel','text/plain'}
    if mime not in accepted: raise HTTPException(400,'File MIME type does not match its extension')
    try:
        if ext=='.pdf':
            if not data.startswith(b'%PDF-'): raise ValueError()
            PdfReader(io.BytesIO(data))
        elif ext=='.docx':
            with zipfile.ZipFile(io.BytesIO(data)) as archive:
                if sum(x.file_size for x in archive.infolist())>100*1024*1024: raise ValueError()
                if 'word/document.xml' not in archive.namelist(): raise ValueError()
        else:
            text=data.decode('utf-8-sig')
            if '\x00' in text: raise ValueError()
    except Exception: raise HTTPException(400,'File content is invalid or unsupported')
    return ext,MIMES[ext]
def extract(filename,data):
    ext=Path(filename).suffix.lower()
    if ext=='.pdf': return [(i+1,p.extract_text() or '') for i,p in enumerate(PdfReader(io.BytesIO(data)).pages)]
    if ext=='.docx':
        doc=Docx(io.BytesIO(data))
        text='\n'.join(p.text for p in doc.paragraphs)+'\n'+'\n'.join(' | '.join(c.text for c in row.cells) for table in doc.tables for row in table.rows)
        return [(None,text)]
    return [(None,data.decode('utf-8-sig'))]
def chunk_text(text,size=180,overlap=35):
    tokens=text.split()
    result=[]
    for i in range(0,len(tokens),size-overlap):
        result.append(' '.join(tokens[i:i+size]))
        if i+size>=len(tokens): break
    return result
def metadata(text,doc):
    def field(label):
        match=re.search(r'(?im)^'+re.escape(label)+r'\s*:\s*(.+)$',text)
        return match.group(1).strip() if match else 'Not identified in source'
    return {'title':doc.title,'authors':field('Authors'),'organization':field('Organization'),'publication_date':field('Date'),'expedition':field('Expedition'),'region':doc.region,'station':field('Station'),'domain':doc.domain,'keywords':list(dict.fromkeys(w for w in words(text) if len(w)>6))[:12],'abstract':field('Abstract'),'objective':field('Objective'),'methodology':field('Methodology'),'findings':field('Findings'),'limitations':field('Limitations'),'datasets':field('Datasets'),'references':field('References'),'extraction':'Deterministic metadata extraction; missing fields are not inferred.'}
def process_job(job_id):
    with SessionLocal() as db:
        job=db.get(Job,job_id)
        if not job: return
        claim=db.execute(update(Job).where(Job.id==job_id,Job.status=='QUEUED').values(status='PROCESSING',updated_at=now()))
        if not claim.rowcount: return
        doc=db.get(Document,job.document_id); doc.processing='PROCESSING'; db.commit()
        try:
            version=db.scalar(select(Version).where(Version.document_id==doc.id,Version.number==doc.version))
            pages=extract(version.filename,storage().get(version.storage_key))
            text='\n'.join(p[1] for p in pages).strip()
            if not text: raise ValueError('No extractable text. Scanned PDFs require OCR before upload.')
            db.execute(delete(Chunk).where(Chunk.document_id==doc.id,Chunk.version==doc.version))
            provider=embeddings(); pos=0
            for page,content in pages:
                for chunk in chunk_text(content):
                    db.add(Chunk(document_id=doc.id,version=doc.version,page=page,position=pos,text=chunk,embedding=provider.embed(chunk))); pos+=1
            doc.meta=metadata(text,doc); doc.abstract=doc.meta['abstract'] if doc.meta['abstract']!='Not identified in source' else text[:450]
            doc.processing='COMPLETED'; job.status='COMPLETED'; job.updated_at=now()
            notify(db,doc.owner_id,f'Processing completed: {doc.title}. Submission awaits publication approval.')
            db.commit()
        except Exception as exc:
            db.rollback(); job=db.get(Job,job_id); doc=db.get(Document,job.document_id)
            job.status='FAILED'; job.error=str(exc)[:500]; job.updated_at=now(); doc.processing='FAILED'
            notify(db,doc.owner_id,f'Processing failed: {doc.title}. {job.error}'); db.commit()
