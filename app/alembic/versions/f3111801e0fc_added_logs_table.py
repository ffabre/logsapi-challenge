"""Added logs table

Revision ID: f3111801e0fc
Revises: 
Create Date: 2024-06-16 11:10:18.629225

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'f3111801e0fc'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('log_entries',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('message', sa.Text(), nullable=True),
    sa.Column('level', sa.String(), nullable=True),
    sa.Column('timestamp', sa.DateTime(timezone=True), nullable=True),
    sa.PrimaryKeyConstraint('id')
    )
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_table('log_entries')
    # ### end Alembic commands ###