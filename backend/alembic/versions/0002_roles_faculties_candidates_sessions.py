from alembic import op
import sqlalchemy as sa

revision = "0002"
down_revision = "0001_initial"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "faculties",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("name", sa.String(length=150), nullable=False, unique=True),
    )
    op.create_index("ix_faculties_id", "faculties", ["id"])

    # Users: replace faculty (text) with faculty_id FK if existed; here we add column
    op.add_column("users", sa.Column("faculty_id", sa.Integer(), nullable=True))
    op.create_foreign_key(
        "fk_users_faculty_id_faculties",
        source_table="users",
        referent_table="faculties",
        local_cols=["faculty_id"],
        remote_cols=["id"],
        ondelete="SET NULL",
    )

    op.create_table(
        "candidates",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("first_name", sa.String(length=100), nullable=False),
        sa.Column("last_name", sa.String(length=100), nullable=False),
        sa.Column("vk_id", sa.String(length=100), nullable=False, unique=True),
        sa.Column("tg_id", sa.String(length=100), nullable=True, unique=True),
        sa.Column("faculty_id", sa.Integer(), nullable=True),
        sa.ForeignKeyConstraint(["faculty_id"], ["faculties.id"], ondelete="SET NULL"),
    )
    op.create_index("ix_candidates_id", "candidates", ["id"])

    op.create_table(
        "interview_sessions",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("faculty_id", sa.Integer(), nullable=False),
        sa.Column("slot_date", sa.Date(), nullable=False),
        sa.Column("start_time", sa.Time(), nullable=False),
        sa.Column("end_time", sa.Time(), nullable=False),
        sa.Column("interviewer_exp_id", sa.Integer(), nullable=True),
        sa.Column("interviewer_new_id", sa.Integer(), nullable=True),
        sa.Column("candidate_id", sa.Integer(), nullable=True),
        sa.ForeignKeyConstraint(["faculty_id"], ["faculties.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["interviewer_exp_id"], ["users.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["interviewer_new_id"], ["users.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["candidate_id"], ["candidates.id"], ondelete="SET NULL"),
        sa.UniqueConstraint("faculty_id", "slot_date", "start_time", name="uq_faculty_date_time"),
    )
    op.create_index("ix_interview_sessions_id", "interview_sessions", ["id"])


def downgrade() -> None:
    op.drop_table("interview_sessions")
    op.drop_table("candidates")
    op.drop_constraint("fk_users_faculty_id_faculties", "users", type_="foreignkey")
    op.drop_column("users", "faculty_id")
    op.drop_table("faculties")

