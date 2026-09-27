import os, time
from collections import Counter
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select, func
from app.models.database import *
from app.core.security import current_user, require_user, moderator, admin, researcher
from app.repositories.documents import get_document, visible_query, serialize, audit, notify
from app.services.retrieval import retrieve
from app.ai.providers import llm
from app.schemas.requests import Chat, Generate, QuizAnswers, UserEdit
from app.core.config import DATA, DEMO_MODE
router=APIRouter(tags=['Research tools'])
def resource(r): return {'id':r.id,'title':r.title,**r.data}
def resources(db,kind): return [resource(r) for r in db.scalars(select(Resource).where(Resource.kind==kind))]
@router.get('/stations')
def stations(db=Depends(get_db)): return resources(db,'station')
@router.get('/expeditions')
def expeditions(db=Depends(get_db)): return resources(db,'expedition')
@router.get('/expeditions/{item_id}')
def expedition(item_id:str,user=Depends(current_user),db=Depends(get_db)):
    r=db.get(Resource,item_id)
    if not r or r.kind!='expedition': raise HTTPException(404,'Expedition not found')
    return {**resource(r),'documents':[serialize(d) for d in db.scalars(visible_query(user)) if d.meta.get('expedition')==r.title]}
@router.get('/datasets')
def datasets(db=Depends(get_db)): return resources(db,'dataset')
@router.get('/datasets/{item_id}/download')
def dataset_download(item_id:str,db=Depends(get_db)):
    from fastapi.responses import Response
    r=db.get(Resource,item_id)
    if not r or r.kind!='dataset': raise HTTPException(404,'Dataset not found')
    db.add(Event(kind='download',value=r.id)); db.commit()
    return Response(r.data['csv'],media_type='text/csv',headers={'Content-Disposition':'attachment; filename="synthetic-polar-observations.csv"'})
@router.get('/media')
def media(db=Depends(get_db)):
    return [{k:v for k,v in item.items() if k!='storage_key'} for item in resources(db,'media') if item.get('status')=='PUBLISHED']
@router.get('/map/features')
def map_features(user=Depends(current_user),db=Depends(get_db)):
    docs=list(db.scalars(visible_query(user)))
    return {'type':'FeatureCollection','features':[{'type':'Feature','geometry':{'type':'Point','coordinates':[s['lon'],s['lat']]},'properties':{**s,'reports':[serialize(d) for d in docs if d.meta.get('station')==s['title']]}} for s in resources(db,'station')],'routes':resources(db,'expedition'),'datasets':resources(db,'dataset')}
@router.post('/chat')
def chat(body:Chat,user=Depends(researcher),db=Depends(get_db)):
    if body.document_id: get_document(db,body.document_id,user)
    if body.conversation_id:
        conv=db.get(Conversation,body.conversation_id)
        if not conv or conv.user_id!=user.id: raise HTTPException(404,'Conversation not found')
    else:
        conv=Conversation(user_id=user.id,title=body.question[:100]); db.add(conv); db.flush()
    sources=retrieve(db,body.question,user,body.document_id,top_k=4)
    try: answer=llm().answer(body.question,sources)
    except Exception: raise HTTPException(503,'AI provider unavailable. Check provider configuration.')
    db.add_all([Message(conversation_id=conv.id,role='user',content=body.question),Message(conversation_id=conv.id,role='assistant',content=answer,sources=sources),Event(kind='chat',value=body.question[:100])]); db.commit()
    return {'conversation_id':conv.id,'answer':answer,'sources':sources,'mode':os.getenv('LLM_PROVIDER','mock'),'related_questions':['What methodology was used?','Which datasets support these findings?','What limitations are reported?']}
@router.get('/chat/conversations')
def conversations(user=Depends(require_user),db=Depends(get_db)):
    return [{'id':c.id,'title':c.title} for c in db.scalars(select(Conversation).where(Conversation.user_id==user.id).order_by(Conversation.created_at.desc()))]
@router.get('/chat/conversations/{conv_id}')
def history(conv_id:str,user=Depends(require_user),db=Depends(get_db)):
    conv=db.get(Conversation,conv_id)
    if not conv or conv.user_id!=user.id: raise HTTPException(404,'Conversation not found')
    result=[]
    for m in db.scalars(select(Message).where(Message.conversation_id==conv_id).order_by(Message.created_at)):
        sources=[]
        for s in m.sources:
            try:
                doc=get_document(db,s['document_id'],user)
                chunk=db.get(Chunk,s['chunk_id'])
                if not chunk: continue
                if chunk.version!=doc.version and doc.owner_id!=user.id and user.role not in ('admin','content_manager'): continue
                sources.append(s)
            except HTTPException: pass
        # Never expose old assistant text after a cited source loses access.
        content=m.content if len(sources)==len(m.sources) else 'A source is no longer available to you. Ask again using your currently accessible sources.'
        result.append({'role':m.role,'content':content,'sources':sources})
    return result
@router.post('/ai/summarize')
def summarize(body:Chat,user=Depends(researcher),db=Depends(get_db)):
    if not body.document_id: raise HTTPException(422,'Select a document')
    doc=get_document(db,body.document_id,user)
    return {'title':doc.title,'summary':doc.abstract,'analysis':doc.meta,'mode':'Extracted source metadata'}
@router.post('/ai/generate-content')
def generate(body:Generate,user=Depends(researcher),db=Depends(get_db)):
    doc=get_document(db,body.document_id,user)
    if doc.processing!='COMPLETED': raise HTTPException(409,'Wait for document processing')
    if os.getenv('LLM_PROVIDER','mock')=='mock':
        opening={'School students':'Explore a question from polar science.','College students':'Explore the research and its methods.','Researchers':'Source-based research brief.','General public':'A closer look at polar science.','Government officials':'Research evidence brief for public communication.'}[body.audience]
        finding=doc.meta.get('findings',doc.abstract)
        text=f'AI-generated · Demo Mode · {body.format}\nAudience: {body.audience} · Tone: {body.tone}\n\n{doc.title}\n\n{opening}\n\n{doc.abstract}\n\nSource finding: {finding}\n\nLimitations: {doc.meta.get("limitations","Not identified in source")}\n\nSource: {doc.title}. '+('Synthetic demonstration material; not official scientific evidence.' if doc.demo else 'Verify this draft against the original source before publication.')
        if body.format in ('Social media post','Instagram caption','LinkedIn post','X/Twitter post'): text=f'AI-generated · Demo Mode\n\n{doc.title}: {finding}'[:245]+'\n#PolarScience'
        if body.format=='Short video script': text='AI-generated · Demo Mode\n\n[Opening: polar research]\n'+opening+'\n\n[Narration]\n'+doc.abstract+'\n\n[On-screen source]\n'+doc.title
    else:
        text=llm().answer(f'Create a {body.format} for {body.audience}, tone {body.tone}. Label AI-generated.',[{'title':doc.title,'excerpt':doc.abstract+' '+str(doc.meta)}])
    generation=Generation(user_id=user.id,document_id=doc.id,format=body.format,content=text); db.add(generation); db.add(Event(kind='generation',value=body.format)); db.commit()
    return {'id':generation.id,'content':text,'status':generation.status,'source':doc.id}
@router.get('/ai/generations')
def generations(user=Depends(require_user),db=Depends(get_db)):
    query=select(Generation)
    if user.role not in ('admin','content_manager'): query=query.where(Generation.user_id==user.id)
    return [{'id':g.id,'format':g.format,'content':g.content,'status':g.status} for g in db.scalars(query)]
@router.post('/ai/generations/{item_id}/publish')
def publish_generation(item_id:str,user=Depends(moderator),db=Depends(get_db)):
    g=db.get(Generation,item_id)
    if not g: raise HTTPException(404,'Draft not found')
    doc=get_document(db,g.document_id,user)
    if doc.moderation!='PUBLISHED' or doc.visibility!='public': raise HTTPException(409,'Publish the public source document first')
    g.status='PUBLISHED'; audit(db,user,'outreach.publish',g.id); db.commit(); return {'ok':True}
@router.get('/outreach')
def outreach(db=Depends(get_db)):
    allowed={d.id for d in db.scalars(visible_query())}
    return [{'id':g.id,'format':g.format,'content':g.content} for g in db.scalars(select(Generation).where(Generation.status=='PUBLISHED')) if g.document_id in allowed]
@router.get('/education')
def education(db=Depends(get_db)): return {'lessons':resources(db,'lesson'),'glossary':resources(db,'glossary')}
@router.get('/quizzes')
def quizzes(db=Depends(get_db)):
    return [{**resource(r),'questions':[{k:v for k,v in q.items() if k not in ('answer','explanation')} for q in r.data['questions']]} for r in db.scalars(select(Resource).where(Resource.kind=='quiz'))]
@router.post('/quizzes/{quiz_id}/attempts')
def attempt(quiz_id:str,body:QuizAnswers,user=Depends(current_user),db=Depends(get_db)):
    quiz=db.get(Resource,quiz_id)
    if not quiz or quiz.kind!='quiz': raise HTTPException(404,'Quiz not found')
    questions=quiz.data['questions']
    if len(body.answers)!=len(questions) or any(a<0 or a>=len(q['options']) for a,q in zip(body.answers,questions)): raise HTTPException(422,'Answer every question')
    score=sum(a==q['answer'] for a,q in zip(body.answers,questions)); db.add(Attempt(user_id=user.id if user else None,quiz_id=quiz.id,score=score,total=len(questions)))
    if user: notify(db,user.id,f'Quiz completed: {score}/{len(questions)}. '+('Polar Explorer achievement earned!' if score==len(questions) else 'Keep exploring polar science.'))
    db.commit(); return {'score':score,'total':len(questions),'achievement':'Polar Explorer' if score==len(questions) else None,'review':questions}
@router.get('/education/progress')
def progress(user=Depends(require_user),db=Depends(get_db)):
    return [{'score':a.score,'total':a.total,'created_at':a.created_at,'quiz_id':a.quiz_id} for a in db.scalars(select(Attempt).where(Attempt.user_id==user.id))]
@router.post('/ai/generate-quiz')
def generate_quiz(body:Chat,user=Depends(moderator),db=Depends(get_db)):
    doc=get_document(db,body.document_id,user)
    if doc.moderation!='PUBLISHED' or doc.visibility!='public': raise HTTPException(409,'An approved public source is required')
    question={'question':f'Which region does “{doc.title}” study?','options':['Arctic','Antarctic'],'answer':0 if doc.region=='Arctic' else 1,'explanation':f'Source metadata identifies {doc.region}.','source_id':doc.id}
    quiz=Resource(kind='quiz',title='Source quiz: '+doc.title,data={'difficulty':'Beginner','demo':True,'questions':[question]}); db.add(quiz); audit(db,user,'quiz.generate',doc.id); db.commit(); return resource(quiz)
@router.get('/analytics/dashboard')
def dashboard(user=Depends(current_user),db=Depends(get_db)):
    docs=list(db.scalars(visible_query(user))); counts=Counter(d.domain for d in docs); years=Counter(d.year for d in docs); regions=Counter(d.region for d in docs)
    privileged=user and user.role in ('admin','content_manager')
    events=list(db.scalars(select(Event))) if privileged else []
    return {'documents':len(docs),'expeditions':len(resources(db,'expedition')),'datasets':len(resources(db,'dataset')),'stations':len(resources(db,'station')),'publications':sum(d.category in ('Research Papers','Publications') for d in docs),'downloads':sum(d.downloads for d in docs),'domains':[{'name':k,'value':v} for k,v in counts.items()],'years':[{'year':str(y),'publications':n} for y,n in sorted(years.items())],'regions':[{'name':k,'value':v} for k,v in regions.items()],'popular':[{'title':d.title,'views':d.views} for d in sorted(docs,key=lambda d:d.views,reverse=True)[:5]],'searches':[{'topic':k,'count':v} for k,v in Counter(e.value for e in events if e.kind=='search').most_common(5)],'ai_usage':sum(e.kind=='chat' for e in events),'uploads':[{'date':k,'count':v} for k,v in sorted(Counter(d.created_at[:10] for d in docs).items())],'demo':True}
@router.get('/analytics/trends')
def trends(user=Depends(current_user),db=Depends(get_db)):
    data=dashboard(user,db)
    return {'label':'Observed repository trends','interpretation':'Counts describe this repository only. They do not establish scientific or global research trends.','domains':data['domains'],'years':data['years'],'regions':data['regions']}
@router.get('/notifications')
def notifications(user=Depends(require_user),db=Depends(get_db)):
    return [{'id':n.id,'text':n.text,'read':n.read,'created_at':n.created_at} for n in db.scalars(select(Notification).where(Notification.user_id==user.id).order_by(Notification.created_at.desc()).limit(50))]
@router.post('/notifications/{item_id}/read')
def mark_read(item_id:str,user=Depends(require_user),db=Depends(get_db)):
    n=db.get(Notification,item_id)
    if not n or n.user_id!=user.id: raise HTTPException(404,'Notification not found')
    n.read=True; db.commit(); return {'ok':True}
@router.get('/users')
def users(user=Depends(admin),db=Depends(get_db)):
    return [{'id':u.id,'name':u.name,'email':u.email,'role':u.role,'active':u.active} for u in db.scalars(select(User))]
@router.put('/users/{item_id}')
def update_user(item_id:str,body:UserEdit,user=Depends(admin),db=Depends(get_db)):
    target=db.get(User,item_id)
    if not target: raise HTTPException(404,'User not found')
    if target.id==user.id and (body.role!='admin' or not body.active): raise HTTPException(409,'You cannot remove your own administrator access')
    target.role=body.role; target.active=body.active
    for session in db.scalars(select(RefreshSession).where(RefreshSession.user_id==target.id)): session.revoked=True
    audit(db,user,'user.permissions',target.id); notify(db,target.id,'Your account permissions were updated.'); db.commit(); return {'ok':True}
@router.get('/audit-logs')
def logs(user=Depends(admin),db=Depends(get_db)):
    return [{'id':a.id,'action':a.action,'target':a.target,'user_id':a.user_id,'created_at':a.created_at} for a in db.scalars(select(Audit).order_by(Audit.created_at.desc()).limit(200))]
@router.get('/health')
@router.get('/health/database')
def health(db=Depends(get_db)):
    db.execute(select(1)); return {'status':'ok','database':'connected'}
@router.get('/health/ai')
def ai_health(): return {'provider':os.getenv('LLM_PROVIDER','mock'),'embedding_provider':os.getenv('EMBEDDING_PROVIDER','mock'),'demo':os.getenv('LLM_PROVIDER','mock')=='mock'}
@router.get('/health/worker')
def worker_health():
    path=DATA/'worker-heartbeat'; age=time.time()-float(path.read_text()) if path.exists() else None
    return {'status':'ok' if age is not None and age<15 else 'offline','heartbeat_age':age}
@router.get('/demo/accounts')
def demo_accounts():
    import json
    if not DEMO_MODE: raise HTTPException(404)
    path=DATA/'demo-accounts.json'
    return json.loads(path.read_text()) if path.exists() else []
