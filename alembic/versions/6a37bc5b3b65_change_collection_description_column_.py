"""change collection description column type

Revision ID: 6a37bc5b3b65
Revises: 7016c1bf3fbf
Create Date: 2023-10-11 14:12:02.331801

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '6a37bc5b3b65'
down_revision = '7016c1bf3fbf'
branch_labels = None
depends_on = None


def upgrade():
    op.alter_column(
        schema="data",
        table_name="collections",
        column_name="description",
        type_=sa.Text,
    )


def downgrade():
    op.alter_column(
        schema="data",
        table_name="collections",
        column_name="description",
        type_=sa.VARCHAR(1024),
    )
