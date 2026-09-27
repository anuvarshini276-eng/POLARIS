"""Initial persistent research schema."""
from alembic import op
from app.models.database import Base
revision='001'
down_revision=None
branch_labels=None
depends_on=None
def upgrade():
    bind=op.get_bind()
    if bind.dialect.name=='postgresql': op.execute('CREATE EXTENSION IF NOT EXISTS vector')
    Base.metadata.create_all(bind)
    if bind.dialect.name=='postgresql':
        op.execute('CREATE INDEX IF NOT EXISTS document_chunks_embedding_hnsw ON document_chunks USING hnsw (embedding vector_cosine_ops)')
def downgrade(): Base.metadata.drop_all(op.get_bind())
