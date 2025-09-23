from alembic import op
import sqlalchemy as sa

revision = "0001_initial"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "users",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("username", sa.String(length=100), nullable=False, unique=True),
        sa.Column("password_hash", sa.String(length=255), nullable=False),
        sa.Column("full_name", sa.String(length=200), nullable=True),
        sa.Column("tg_id", sa.String(length=100), nullable=True, unique=True),
        sa.Column("faculty", sa.String(length=100), nullable=True),
        sa.Column("role", sa.String(length=50), nullable=False, server_default="interviewer"),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.sql.expression.true()),
    )
    op.create_index("ix_users_id", "users", ["id"])
    op.create_index("ix_users_username", "users", ["username"])

    op.create_table(
        "timeslots",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("slot_date", sa.Date(), nullable=False),
        sa.Column("start_time", sa.Time(), nullable=False),
        sa.Column("end_time", sa.Time(), nullable=False),
        sa.Column("is_gas", sa.Boolean(), nullable=False, server_default=sa.sql.expression.false()),
        sa.UniqueConstraint("user_id", "slot_date", "start_time", name="uq_user_date_time"),
    )
    op.create_index("ix_timeslots_id", "timeslots", ["id"])


def downgrade() -> None:
    op.drop_table("timeslots")
    op.drop_table("users")

