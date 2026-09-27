"""Keep application tables inaccessible to unprivileged hosted database clients."""
from alembic import op
from app.models.database import Base

revision = '002'
down_revision = '001'
branch_labels = None
depends_on = None

def upgrade():
    bind = op.get_bind()
    if bind.dialect.name == 'postgresql':
        for table in Base.metadata.sorted_tables:
            name = bind.dialect.identifier_preparer.quote(table.name)
            op.execute(f'ALTER TABLE {name} ENABLE ROW LEVEL SECURITY')

def downgrade():
    bind = op.get_bind()
    if bind.dialect.name == 'postgresql':
        for table in Base.metadata.sorted_tables:
            name = bind.dialect.identifier_preparer.quote(table.name)
            op.execute(f'ALTER TABLE {name} DISABLE ROW LEVEL SECURITY')
