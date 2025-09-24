from alembic import op
import sqlalchemy as sa

revision = "0003_add_faculties_admin_invites"
down_revision = "0002"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Добавляем колонку google_sheet_url к существующей таблице faculties
    op.add_column('faculties', sa.Column('google_sheet_url', sa.Text(), nullable=True))
    
    # Создаем таблицу admin_invites
    op.create_table(
        "admin_invites",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("faculty_id", sa.Integer(), nullable=False),
        sa.Column("invite_code", sa.String(length=50), nullable=False, unique=True),
        sa.Column("is_used", sa.Boolean(), nullable=False, default=False),
        sa.Column("created_at", sa.String(length=50), nullable=False),
        sa.ForeignKeyConstraint(["faculty_id"], ["faculties.id"]),
    )
    op.create_index("ix_admin_invites_id", "admin_invites", ["id"])


def downgrade() -> None:
    op.drop_table("admin_invites")
    op.drop_column('faculties', 'google_sheet_url')
