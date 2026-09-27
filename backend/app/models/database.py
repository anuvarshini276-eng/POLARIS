import uuid, os
from datetime import datetime, timezone
from sqlalchemy import create_engine, event, String, Text, Integer, ForeignKey, JSON, Boolean, Float, UniqueConstraint
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, sessionmaker
from app.core.config import DATABASE_URL
from pgvector.sqlalchemy import Vector

def now(): return datetime.now(timezone.utc).isoformat()
def uid(): return str(uuid.uuid4())
engine = create_engine(DATABASE_URL, connect_args={'check_same_thread': False, 'timeout': 30} if DATABASE_URL.startswith('sqlite') else {}, pool_pre_ping=True)
if DATABASE_URL.startswith('sqlite'):
    @event.listens_for(engine, 'connect')
    def sqlite_setup(connection, _):
        connection.execute('PRAGMA foreign_keys=ON')
        connection.execute('PRAGMA journal_mode=WAL')
SessionLocal = sessionmaker(engine, expire_on_commit=False)
class Base(DeclarativeBase): pass
class Entity:
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=uid)
    created_at: Mapped[str] = mapped_column(String, default=now, index=True)
class User(Entity, Base):
    __tablename__='users'
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    name: Mapped[str] = mapped_column(String(100))
    password: Mapped[str] = mapped_column(Text)
    role: Mapped[str] = mapped_column(String(30), default='researcher')
    active: Mapped[bool] = mapped_column(Boolean, default=True)
    failures: Mapped[int] = mapped_column(Integer, default=0)
    locked_until: Mapped[float] = mapped_column(Float, default=0)
class RefreshSession(Entity, Base):
    __tablename__='refresh_sessions'
    user_id: Mapped[str] = mapped_column(ForeignKey('users.id'), index=True)
    token_hash: Mapped[str] = mapped_column(String, unique=True)
    expires: Mapped[float] = mapped_column(Float)
    revoked: Mapped[bool] = mapped_column(Boolean, default=False)
class Document(Entity, Base):
    __tablename__='documents'
    title: Mapped[str] = mapped_column(String(300), index=True)
    owner_id: Mapped[str] = mapped_column(ForeignKey('users.id'), index=True)
    category: Mapped[str] = mapped_column(String, default='Research Papers')
    region: Mapped[str] = mapped_column(String, default='Antarctic', index=True)
    domain: Mapped[str] = mapped_column(String, default='Climate science', index=True)
    year: Mapped[int] = mapped_column(Integer, default=2025, index=True)
    visibility: Mapped[str] = mapped_column(String, default='public')
    moderation: Mapped[str] = mapped_column(String, default='UPLOADED', index=True)
    processing: Mapped[str] = mapped_column(String, default='UPLOADED')
    meta: Mapped[dict] = mapped_column(JSON, default=dict)
    abstract: Mapped[str] = mapped_column(Text, default='')
    version: Mapped[int] = mapped_column(Integer, default=1)
    downloads: Mapped[int] = mapped_column(Integer, default=0)
    views: Mapped[int] = mapped_column(Integer, default=0)
    demo: Mapped[bool] = mapped_column(Boolean, default=False)
    deleted: Mapped[bool] = mapped_column(Boolean, default=False)
class Version(Entity, Base):
    __tablename__='document_versions'
    document_id: Mapped[str] = mapped_column(ForeignKey('documents.id'), index=True)
    number: Mapped[int] = mapped_column(Integer)
    filename: Mapped[str] = mapped_column(String)
    storage_key: Mapped[str] = mapped_column(String)
    mime: Mapped[str] = mapped_column(String)
    size: Mapped[int] = mapped_column(Integer)
    __table_args__=(UniqueConstraint('document_id','number'),)
class Chunk(Entity, Base):
    __tablename__='document_chunks'
    document_id: Mapped[str] = mapped_column(ForeignKey('documents.id'), index=True)
    version: Mapped[int] = mapped_column(Integer)
    page: Mapped[int | None] = mapped_column(Integer, nullable=True)
    position: Mapped[int] = mapped_column(Integer)
    text: Mapped[str] = mapped_column(Text)
    embedding: Mapped[list] = mapped_column(JSON().with_variant(Vector(int(os.getenv('EMBEDDING_DIMENSIONS','256'))),'postgresql'))
class Job(Entity, Base):
    __tablename__='processing_jobs'
    document_id: Mapped[str] = mapped_column(ForeignKey('documents.id'), index=True)
    status: Mapped[str] = mapped_column(String, default='QUEUED', index=True)
    error: Mapped[str] = mapped_column(Text, default='')
    updated_at: Mapped[str] = mapped_column(String, default=now)
class Resource(Entity, Base):
    __tablename__='resources'
    kind: Mapped[str] = mapped_column(String, index=True)
    title: Mapped[str] = mapped_column(String)
    data: Mapped[dict] = mapped_column(JSON, default=dict)
class Conversation(Entity, Base):
    __tablename__='conversations'
    user_id: Mapped[str] = mapped_column(ForeignKey('users.id'), index=True)
    title: Mapped[str] = mapped_column(String)
class Message(Entity, Base):
    __tablename__='chat_messages'
    conversation_id: Mapped[str] = mapped_column(ForeignKey('conversations.id'), index=True)
    role: Mapped[str] = mapped_column(String)
    content: Mapped[str] = mapped_column(Text)
    sources: Mapped[list] = mapped_column(JSON, default=list)
class Generation(Entity, Base):
    __tablename__='ai_generations'
    user_id: Mapped[str] = mapped_column(ForeignKey('users.id'), index=True)
    document_id: Mapped[str] = mapped_column(ForeignKey('documents.id'))
    format: Mapped[str] = mapped_column(String)
    content: Mapped[str] = mapped_column(Text)
    status: Mapped[str] = mapped_column(String, default='DRAFT')
class Attempt(Entity, Base):
    __tablename__='quiz_attempts'
    user_id: Mapped[str | None] = mapped_column(ForeignKey('users.id'), nullable=True)
    quiz_id: Mapped[str] = mapped_column(ForeignKey('resources.id'))
    score: Mapped[int] = mapped_column(Integer)
    total: Mapped[int] = mapped_column(Integer)
class Notification(Entity, Base):
    __tablename__='notifications'
    user_id: Mapped[str] = mapped_column(ForeignKey('users.id'), index=True)
    text: Mapped[str] = mapped_column(Text)
    read: Mapped[bool] = mapped_column(Boolean, default=False)
class Audit(Entity, Base):
    __tablename__='audit_logs'
    user_id: Mapped[str | None] = mapped_column(String, nullable=True)
    action: Mapped[str] = mapped_column(String)
    target: Mapped[str] = mapped_column(String)
class Event(Entity, Base):
    __tablename__='analytics_events'
    kind: Mapped[str] = mapped_column(String, index=True)
    value: Mapped[str] = mapped_column(String, default='')

def get_db():
    with SessionLocal() as db: yield db
