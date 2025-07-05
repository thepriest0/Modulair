"""restore learning style

Revision ID: 9d9e5ab958d9
Revises: 707d5ab958d8
Create Date: 2024-03-15 11:00:00.000000

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '9d9e5ab958d9'
down_revision = '707d5ab958d8'
branch_labels = None
depends_on = None

def upgrade():
    # Add learning_style column back to users table
    op.add_column('user', sa.Column('preferred_learning_style', sa.String(50), nullable=True))
    
    # Add learning_style column back to courses table
    op.add_column('course', sa.Column('learning_style', sa.String(50), nullable=False, server_default='Visual'))

def downgrade():
    # Remove learning_style column from users table
    op.drop_column('user', 'preferred_learning_style')
    
    # Remove learning_style column from courses table
    op.drop_column('course', 'learning_style') 