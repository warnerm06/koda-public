"""add JSONB column to photos

Revision ID: ae95c0a737a4
Revises: 
Create Date: 2019-02-05 11:46:54.326570

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'ae95c0a737a4'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    op.add_column('photos', sa.Column('azure_api', sa.dialects.postgresql.JSONB()))


def downgrade():
        op.drop_column('photos', 'azure_api')

