import math
from sqlalchemy import select
from app.models.database import Chunk
from app.repositories.documents import visible_query
from app.ai.providers import embeddings, words

STOP={'the','and','what','were','from','with','this','that','about','show','which','does','research','document','findings','major','summarize','explain','have','between','into','observations','study','studies','are','used','reported','used','these'}
def retrieve(db,question,user=None,document_id=None,top_k=5):
    docs=list(db.scalars(visible_query(user)))
    if document_id: docs=[d for d in docs if d.id==document_id]
    docs={d.id:d for d in docs if d.processing=='COMPLETED'}
    if not docs: return []
    query_tokens=set(words(question))-STOP
    vector=embeddings().embed(question); found=[]
    chunks=select(Chunk).where(Chunk.document_id.in_(docs))
    # PostgreSQL ranks permission-filtered candidates using pgvector; SQLite keeps the portable demo equivalent.
    if db.bind.dialect.name=='postgresql':
        from sqlalchemy import cast
        from pgvector.sqlalchemy import Vector
        chunks=chunks.order_by(cast(Chunk.embedding,Vector(len(vector))).cosine_distance(vector)).limit(300)
    for chunk in db.scalars(chunks):
        doc=docs[chunk.document_id]
        if chunk.version!=doc.version: continue
        tokens=set(words(chunk.text))
        overlap=len(query_tokens & tokens)/max(1,len(query_tokens))
        semantic=sum(a*b for a,b in zip(vector,chunk.embedding)) if len(vector)==len(chunk.embedding) else 0
        score=0.7*overlap+0.3*max(0,semantic)
        if (overlap==0 or score<0.18) and not (document_id and not query_tokens): continue
        sentences=chunk.text.split('. ')
        sentences.sort(key=lambda s:len(set(words(s))&query_tokens),reverse=True)
        excerpt='. '.join(sentences[:3])[:850]
        found.append({'document_id':doc.id,'chunk_id':chunk.id,'version':chunk.version,'title':doc.title,'page':chunk.page,'excerpt':excerpt,'relevance':round(score,3),'url':f'/repository/{doc.id}','demo':doc.demo})
    found.sort(key=lambda s:s['relevance'],reverse=True)
    if found:
        cutoff=max(0.18,found[0]['relevance']*0.65)
        found=[s for s in found if s['relevance']>=cutoff]
    return found[:top_k]
