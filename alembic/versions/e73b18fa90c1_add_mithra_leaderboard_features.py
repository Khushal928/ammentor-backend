"""add mithra leaderboard features, evidence, notifications, and rubric

Revision ID: e73b18fa90c1
Revises: c58f00ff0d67
Create Date: 2026-10-26 21:20:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'e73b18fa90c1'
down_revision: Union[str, None] = 'c58f00ff0d67'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. Add student profile fields to users table
    op.add_column('users', sa.Column('roll_number', sa.String(), nullable=True))
    op.add_column('users', sa.Column('department', sa.String(), nullable=True))
    op.add_column('users', sa.Column('vertical_id', sa.Integer(), nullable=True))
    op.create_index(op.f('ix_users_roll_number'), 'users', ['roll_number'], unique=False)
    op.create_index(op.f('ix_users_department'), 'users', ['department'], unique=False)
    op.create_foreign_key('fk_users_vertical_id', 'users', 'groups', ['vertical_id'], ['id'])

    # 2. Add rejection_reason, info_request, and points to claims table
    op.add_column('claims', sa.Column('rejection_reason', sa.Text(), nullable=True))
    op.add_column('claims', sa.Column('info_request', sa.Text(), nullable=True))
    op.add_column('claims', sa.Column('points', sa.Integer(), nullable=True))

    # 3. Create mentor_verticals association table
    op.create_table(
        'mentor_verticals',
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('group_id', sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(['group_id'], ['groups.id'], ),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('user_id', 'group_id'),
    )

    # 4. Create claim_evidence table
    op.create_table(
        'claim_evidence',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('claim_id', sa.Integer(), nullable=False),
        sa.Column('file_name', sa.String(), nullable=False),
        sa.Column('file_url', sa.String(), nullable=False),
        sa.Column('file_type', sa.String(), nullable=True),
        sa.Column('uploaded_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['claim_id'], ['claims.id'], ),
        sa.PrimaryKeyConstraint('id'),
    )

    # 5. Create notifications table
    op.create_table(
        'notifications',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('title', sa.String(), nullable=False),
        sa.Column('message', sa.Text(), nullable=False),
        sa.Column('claim_id', sa.Integer(), nullable=True),
        sa.Column('is_read', sa.Boolean(), server_default='false', nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['claim_id'], ['claims.id'], ),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_notifications_user_id'), 'notifications', ['user_id'], unique=False)

    # 6. Create claim_rubrics table if not already present
    op.create_table(
        'claim_rubrics',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('event_level', sa.Enum('SCHOOL_DEPARTMENT', 'CAMPUS', 'INTER_CAMPUS', 'STATE', 'NATIONAL', 'INTERNATIONAL', name='eventlevel'), nullable=False),
        sa.Column('participation_category', sa.Enum('PARTICIPANT', 'POSITION_HOLDER', 'ORGANISER_LEAD', 'VOLUNTEER_CORE_TEAM', 'REPRESENTATIVE', name='participationcategory'), nullable=False),
        sa.Column('points', sa.Integer(), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('event_level', 'participation_category', name='uq_rubric_level_category'),
    )


def downgrade() -> None:
    op.drop_table('claim_rubrics')
    op.drop_index(op.f('ix_notifications_user_id'), table_name='notifications')
    op.drop_table('notifications')
    op.drop_table('claim_evidence')
    op.drop_table('mentor_verticals')
    op.drop_column('claims', 'points')
    op.drop_column('claims', 'info_request')
    op.drop_column('claims', 'rejection_reason')
    op.drop_constraint('fk_users_vertical_id', 'users', type_='foreignkey')
    op.drop_index(op.f('ix_users_department'), table_name='users')
    op.drop_index(op.f('ix_users_roll_number'), table_name='users')
    op.drop_column('users', 'vertical_id')
    op.drop_column('users', 'department')
    op.drop_column('users', 'roll_number')
